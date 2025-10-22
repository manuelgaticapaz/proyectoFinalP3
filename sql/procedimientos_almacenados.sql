-- =====================================================
-- PROCEDIMIENTOS ALMACENADOS PARA MEDICITAS PRO
-- Sistema de Gestión de Citas Médicas Multi-Tenant
-- =====================================================

USE proyectodb;

-- Eliminar procedimientos existentes si existen
DROP PROCEDURE IF EXISTS sp_obtener_estadisticas_clinica;
DROP PROCEDURE IF EXISTS sp_obtener_citas_por_periodo;
DROP PROCEDURE IF EXISTS sp_reagendar_cita;
DROP PROCEDURE IF EXISTS sp_verificar_disponibilidad_doctor;
DROP PROCEDURE IF EXISTS sp_obtener_ocupacion_mensual;
DROP PROCEDURE IF EXISTS sp_generar_reporte_doctor;
DROP PROCEDURE IF EXISTS sp_transferir_paciente_clinica;
DROP PROCEDURE IF EXISTS sp_obtener_horarios_disponibles;
DROP PROCEDURE IF EXISTS sp_estadisticas_dashboard;
DROP PROCEDURE IF EXISTS sp_validar_conflicto_citas;

DELIMITER //

-- =====================================================
-- 1. PROCEDIMIENTO: Obtener estadísticas de clínica
-- =====================================================
CREATE PROCEDURE sp_obtener_estadisticas_clinica(
    IN p_clinica_id INT,
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SELECT 
        c.nombre AS nombre_clinica,
        COUNT(a.id) AS total_citas,
        COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS citas_completadas,
        COUNT(CASE WHEN a.estado = 'cancelada' THEN 1 END) AS citas_canceladas,
        COUNT(CASE WHEN a.estado = 'programada' THEN 1 END) AS citas_programadas,
        COUNT(DISTINCT a.paciente_id) AS pacientes_atendidos,
        COUNT(DISTINCT a.doctor_id) AS doctores_activos,
        ROUND(
            (COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) * 100.0) / 
            NULLIF(COUNT(a.id), 0), 2
        ) AS porcentaje_exito
    FROM clinicas_clinica c
    LEFT JOIN appointments_appointment a ON c.id = a.clinica_id 
        AND DATE(a.fecha) BETWEEN p_fecha_inicio AND p_fecha_fin
    WHERE c.id = p_clinica_id AND c.activa = 1
    GROUP BY c.id, c.nombre;
END //

-- =====================================================
-- 2. PROCEDIMIENTO: Obtener citas por período
-- =====================================================
CREATE PROCEDURE sp_obtener_citas_por_periodo(
    IN p_clinica_id INT,
    IN p_doctor_id INT,
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE,
    IN p_estado VARCHAR(20)
)
BEGIN
    DECLARE sql_query TEXT DEFAULT '';
    
    SET sql_query = 'SELECT 
        a.id,
        a.fecha,
        a.motivo,
        a.estado,
        a.observaciones,
        CONCAT(p.nombre, " ", p.apellidos) AS paciente_nombre,
        p.dni AS paciente_dni,
        CONCAT(d.nombre, " ", d.apellidos) AS doctor_nombre,
        d.especialidad,
        c.nombre AS clinica_nombre
    FROM appointments_appointment a
    INNER JOIN patients_patient p ON a.paciente_id = p.id
    INNER JOIN doctors_doctor d ON a.doctor_id = d.id
    INNER JOIN clinicas_clinica c ON a.clinica_id = c.id
    WHERE DATE(a.fecha) BETWEEN ? AND ?';
    
    IF p_clinica_id IS NOT NULL THEN
        SET sql_query = CONCAT(sql_query, ' AND a.clinica_id = ', p_clinica_id);
    END IF;
    
    IF p_doctor_id IS NOT NULL THEN
        SET sql_query = CONCAT(sql_query, ' AND a.doctor_id = ', p_doctor_id);
    END IF;
    
    IF p_estado IS NOT NULL AND p_estado != '' THEN
        SET sql_query = CONCAT(sql_query, ' AND a.estado = "', p_estado, '"');
    END IF;
    
    SET sql_query = CONCAT(sql_query, ' ORDER BY a.fecha ASC');
    
    SET @sql = sql_query;
    PREPARE stmt FROM @sql;
    EXECUTE stmt USING p_fecha_inicio, p_fecha_fin;
    DEALLOCATE PREPARE stmt;
END //

-- =====================================================
-- 3. PROCEDIMIENTO: Reagendar cita con validaciones
-- =====================================================
CREATE PROCEDURE sp_reagendar_cita(
    IN p_cita_id INT,
    IN p_nueva_fecha DATETIME,
    IN p_usuario_id INT,
    OUT p_resultado VARCHAR(100),
    OUT p_codigo_error INT
)
BEGIN
    DECLARE v_doctor_id INT;
    DECLARE v_clinica_id INT;
    DECLARE v_conflictos INT DEFAULT 0;
    DECLARE v_fecha_anterior DATETIME;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_codigo_error = -1;
        SET p_resultado = 'Error interno del sistema';
        ROLLBACK;
    END;
    
    START TRANSACTION;
    
    -- Verificar que la cita existe
    SELECT doctor_id, clinica_id, fecha 
    INTO v_doctor_id, v_clinica_id, v_fecha_anterior
    FROM appointments_appointment 
    WHERE id = p_cita_id;
    
    IF v_doctor_id IS NULL THEN
        SET p_codigo_error = 1;
        SET p_resultado = 'Cita no encontrada';
        ROLLBACK;
    ELSE
        -- Verificar conflictos de horario
        SELECT COUNT(*) INTO v_conflictos
        FROM appointments_appointment
        WHERE doctor_id = v_doctor_id 
        AND fecha = p_nueva_fecha 
        AND id != p_cita_id
        AND estado NOT IN ('cancelada');
        
        IF v_conflictos > 0 THEN
            SET p_codigo_error = 2;
            SET p_resultado = 'Conflicto de horario detectado';
            ROLLBACK;
        ELSE
            -- Actualizar la cita
            UPDATE appointments_appointment 
            SET fecha = p_nueva_fecha,
                estado = 'programada'
            WHERE id = p_cita_id;
            
            -- Registrar el cambio en log (si existe tabla de auditoría)
            -- INSERT INTO auditoria_citas (cita_id, accion, fecha_anterior, fecha_nueva, usuario_id, fecha_cambio)
            -- VALUES (p_cita_id, 'REAGENDAR', v_fecha_anterior, p_nueva_fecha, p_usuario_id, NOW());
            
            SET p_codigo_error = 0;
            SET p_resultado = 'Cita reagendada exitosamente';
            COMMIT;
        END IF;
    END IF;
END //

-- =====================================================
-- 4. PROCEDIMIENTO: Verificar disponibilidad de doctor
-- =====================================================
CREATE PROCEDURE sp_verificar_disponibilidad_doctor(
    IN p_doctor_id INT,
    IN p_fecha DATE,
    IN p_hora_inicio TIME,
    IN p_hora_fin TIME
)
BEGIN
    SELECT 
        TIME(a.fecha) AS hora_ocupada,
        CONCAT(p.nombre, ' ', p.apellidos) AS paciente,
        a.motivo,
        a.estado
    FROM appointments_appointment a
    INNER JOIN patients_patient p ON a.paciente_id = p.id
    WHERE a.doctor_id = p_doctor_id
    AND DATE(a.fecha) = p_fecha
    AND TIME(a.fecha) BETWEEN p_hora_inicio AND p_hora_fin
    AND a.estado NOT IN ('cancelada')
    ORDER BY a.fecha;
END //

-- =====================================================
-- 5. PROCEDIMIENTO: Obtener ocupación mensual
-- =====================================================
CREATE PROCEDURE sp_obtener_ocupacion_mensual(
    IN p_clinica_id INT,
    IN p_año INT,
    IN p_mes INT
)
BEGIN
    SELECT 
        DAY(a.fecha) AS dia,
        COUNT(a.id) AS total_citas,
        COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS completadas,
        COUNT(CASE WHEN a.estado = 'cancelada' THEN 1 END) AS canceladas,
        COUNT(CASE WHEN a.estado = 'programada' THEN 1 END) AS programadas,
        ROUND(
            (COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) * 100.0) / 
            NULLIF(COUNT(a.id), 0), 1
        ) AS porcentaje_ocupacion
    FROM appointments_appointment a
    WHERE a.clinica_id = p_clinica_id
    AND YEAR(a.fecha) = p_año
    AND MONTH(a.fecha) = p_mes
    GROUP BY DAY(a.fecha)
    ORDER BY DAY(a.fecha);
END //

-- =====================================================
-- 6. PROCEDIMIENTO: Generar reporte por doctor
-- =====================================================
CREATE PROCEDURE sp_generar_reporte_doctor(
    IN p_doctor_id INT,
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE
)
BEGIN
    -- Estadísticas generales del doctor
    SELECT 
        CONCAT(d.nombre, ' ', d.apellidos) AS doctor_nombre,
        d.especialidad,
        c.nombre AS clinica_nombre,
        COUNT(a.id) AS total_citas,
        COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS citas_completadas,
        COUNT(CASE WHEN a.estado = 'cancelada' THEN 1 END) AS citas_canceladas,
        COUNT(CASE WHEN a.estado = 'no_asistio' THEN 1 END) AS no_asistieron,
        COUNT(DISTINCT a.paciente_id) AS pacientes_unicos,
        ROUND(AVG(CASE 
            WHEN a.estado = 'completada' THEN 
                TIMESTAMPDIFF(MINUTE, a.fecha, 
                    CASE WHEN a.observaciones IS NOT NULL 
                    THEN DATE_ADD(a.fecha, INTERVAL 30 MINUTE) 
                    ELSE a.fecha END)
            END), 0) AS duracion_promedio_minutos,
        ROUND(
            (COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) * 100.0) / 
            NULLIF(COUNT(a.id), 0), 2
        ) AS porcentaje_exito
    FROM doctors_doctor d
    LEFT JOIN appointments_appointment a ON d.id = a.doctor_id 
        AND DATE(a.fecha) BETWEEN p_fecha_inicio AND p_fecha_fin
    LEFT JOIN clinicas_clinica c ON d.clinica_id = c.id
    WHERE d.id = p_doctor_id
    GROUP BY d.id;
    
    -- Detalle de citas por día
    SELECT 
        DATE(a.fecha) AS fecha,
        COUNT(a.id) AS citas_dia,
        COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS completadas_dia,
        GROUP_CONCAT(
            CONCAT(TIME(a.fecha), ' - ', 
                   SUBSTRING(CONCAT(p.nombre, ' ', p.apellidos), 1, 20),
                   ' (', a.estado, ')')
            ORDER BY a.fecha SEPARATOR '; '
        ) AS detalle_citas
    FROM appointments_appointment a
    INNER JOIN patients_patient p ON a.paciente_id = p.id
    WHERE a.doctor_id = p_doctor_id
    AND DATE(a.fecha) BETWEEN p_fecha_inicio AND p_fecha_fin
    GROUP BY DATE(a.fecha)
    ORDER BY DATE(a.fecha);
END //

-- =====================================================
-- 7. PROCEDIMIENTO: Transferir paciente entre clínicas
-- =====================================================
CREATE PROCEDURE sp_transferir_paciente_clinica(
    IN p_paciente_id INT,
    IN p_clinica_origen_id INT,
    IN p_clinica_destino_id INT,
    IN p_usuario_id INT,
    OUT p_resultado VARCHAR(100),
    OUT p_codigo_error INT
)
BEGIN
    DECLARE v_citas_pendientes INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_codigo_error = -1;
        SET p_resultado = 'Error interno del sistema';
        ROLLBACK;
    END;
    
    START TRANSACTION;
    
    -- Verificar que el paciente existe en la clínica origen
    IF NOT EXISTS (SELECT 1 FROM patients_patient WHERE id = p_paciente_id AND clinica_id = p_clinica_origen_id) THEN
        SET p_codigo_error = 1;
        SET p_resultado = 'Paciente no encontrado en clínica origen';
        ROLLBACK;
    ELSE
        -- Verificar citas pendientes
        SELECT COUNT(*) INTO v_citas_pendientes
        FROM appointments_appointment
        WHERE paciente_id = p_paciente_id
        AND clinica_id = p_clinica_origen_id
        AND fecha > NOW()
        AND estado IN ('programada', 'confirmada');
        
        IF v_citas_pendientes > 0 THEN
            SET p_codigo_error = 2;
            SET p_resultado = CONCAT('El paciente tiene ', v_citas_pendientes, ' citas pendientes');
            ROLLBACK;
        ELSE
            -- Transferir paciente
            UPDATE patients_patient 
            SET clinica_id = p_clinica_destino_id
            WHERE id = p_paciente_id;
            
            -- Actualizar citas históricas
            UPDATE appointments_appointment 
            SET clinica_id = p_clinica_destino_id
            WHERE paciente_id = p_paciente_id;
            
            SET p_codigo_error = 0;
            SET p_resultado = 'Paciente transferido exitosamente';
            COMMIT;
        END IF;
    END IF;
END //

-- =====================================================
-- 8. PROCEDIMIENTO: Obtener horarios disponibles
-- =====================================================
CREATE PROCEDURE sp_obtener_horarios_disponibles(
    IN p_doctor_id INT,
    IN p_fecha DATE,
    IN p_duracion_cita INT
)
BEGIN
    DECLARE v_hora_inicio TIME DEFAULT '08:00:00';
    DECLARE v_hora_fin TIME DEFAULT '18:00:00';
    DECLARE v_intervalo INT DEFAULT 30; -- minutos
    
    -- Obtener configuración de horarios del doctor o clínica
    SELECT 
        COALESCE(d.duracion_cita_default, c.duracion_cita_default, 30),
        COALESCE(c.horario_inicio, '08:00:00'),
        COALESCE(c.horario_fin, '18:00:00')
    INTO v_intervalo, v_hora_inicio, v_hora_fin
    FROM doctors_doctor d
    LEFT JOIN clinicas_clinica c ON d.clinica_id = c.id
    WHERE d.id = p_doctor_id;
    
    -- Generar horarios disponibles
    WITH RECURSIVE horarios AS (
        SELECT v_hora_inicio AS hora
        UNION ALL
        SELECT ADDTIME(hora, SEC_TO_TIME(v_intervalo * 60))
        FROM horarios
        WHERE ADDTIME(hora, SEC_TO_TIME(v_intervalo * 60)) <= v_hora_fin
    )
    SELECT 
        h.hora,
        CASE 
            WHEN a.id IS NULL THEN 'DISPONIBLE'
            ELSE 'OCUPADO'
        END AS estado,
        CASE 
            WHEN a.id IS NOT NULL THEN CONCAT(p.nombre, ' ', p.apellidos)
            ELSE NULL
        END AS paciente_nombre
    FROM horarios h
    LEFT JOIN appointments_appointment a ON DATE(a.fecha) = p_fecha 
        AND TIME(a.fecha) = h.hora 
        AND a.doctor_id = p_doctor_id
        AND a.estado NOT IN ('cancelada')
    LEFT JOIN patients_patient p ON a.paciente_id = p.id
    ORDER BY h.hora;
END //

-- =====================================================
-- 9. PROCEDIMIENTO: Estadísticas para dashboard
-- =====================================================
CREATE PROCEDURE sp_estadisticas_dashboard(
    IN p_clinica_id INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_es_admin BOOLEAN DEFAULT FALSE;
    
    -- Verificar si es administrador
    SELECT COUNT(*) > 0 INTO v_es_admin
    FROM auth_user u
    WHERE u.id = p_usuario_id AND u.is_staff = 1;
    
    -- Estadísticas del día
    SELECT 
        'HOY' AS periodo,
        COUNT(a.id) AS total_citas,
        COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS completadas,
        COUNT(CASE WHEN a.estado = 'programada' THEN 1 END) AS programadas,
        COUNT(CASE WHEN a.estado = 'cancelada' THEN 1 END) AS canceladas
    FROM appointments_appointment a
    WHERE DATE(a.fecha) = CURDATE()
    AND (p_clinica_id IS NULL OR a.clinica_id = p_clinica_id)
    
    UNION ALL
    
    -- Estadísticas del mes
    SELECT 
        'MES_ACTUAL' AS periodo,
        COUNT(a.id) AS total_citas,
        COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS completadas,
        COUNT(CASE WHEN a.estado = 'programada' THEN 1 END) AS programadas,
        COUNT(CASE WHEN a.estado = 'cancelada' THEN 1 END) AS canceladas
    FROM appointments_appointment a
    WHERE YEAR(a.fecha) = YEAR(CURDATE()) 
    AND MONTH(a.fecha) = MONTH(CURDATE())
    AND (p_clinica_id IS NULL OR a.clinica_id = p_clinica_id);
    
    -- Próximas citas (siguientes 7 días)
    SELECT 
        DATE(a.fecha) AS fecha,
        COUNT(a.id) AS citas_programadas,
        GROUP_CONCAT(
            CONCAT(TIME(a.fecha), ' - ', d.nombre, ' ', d.apellidos)
            ORDER BY a.fecha SEPARATOR '; '
        ) AS detalle
    FROM appointments_appointment a
    INNER JOIN doctors_doctor d ON a.doctor_id = d.id
    WHERE DATE(a.fecha) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
    AND a.estado = 'programada'
    AND (p_clinica_id IS NULL OR a.clinica_id = p_clinica_id)
    GROUP BY DATE(a.fecha)
    ORDER BY DATE(a.fecha)
    LIMIT 7;
END //

-- =====================================================
-- 10. PROCEDIMIENTO: Validar conflictos de citas
-- =====================================================
CREATE PROCEDURE sp_validar_conflicto_citas(
    IN p_doctor_id INT,
    IN p_fecha DATETIME,
    IN p_duracion INT,
    IN p_cita_id_excluir INT,
    OUT p_hay_conflicto BOOLEAN,
    OUT p_detalles_conflicto TEXT
)
BEGIN
    DECLARE v_fecha_fin DATETIME;
    DECLARE v_conflictos INT DEFAULT 0;
    
    SET v_fecha_fin = DATE_ADD(p_fecha, INTERVAL p_duracion MINUTE);
    
    -- Buscar conflictos
    SELECT 
        COUNT(*),
        GROUP_CONCAT(
            CONCAT('Cita a las ', TIME(a.fecha), ' con ', p.nombre, ' ', p.apellidos)
            SEPARATOR '; '
        )
    INTO v_conflictos, p_detalles_conflicto
    FROM appointments_appointment a
    INNER JOIN patients_patient p ON a.paciente_id = p.id
    WHERE a.doctor_id = p_doctor_id
    AND a.estado NOT IN ('cancelada')
    AND (p_cita_id_excluir IS NULL OR a.id != p_cita_id_excluir)
    AND (
        (a.fecha BETWEEN p_fecha AND v_fecha_fin)
        OR (DATE_ADD(a.fecha, INTERVAL 30 MINUTE) BETWEEN p_fecha AND v_fecha_fin)
        OR (p_fecha BETWEEN a.fecha AND DATE_ADD(a.fecha, INTERVAL 30 MINUTE))
    );
    
    SET p_hay_conflicto = (v_conflictos > 0);
    
    IF NOT p_hay_conflicto THEN
        SET p_detalles_conflicto = 'No hay conflictos detectados';
    END IF;
END //

DELIMITER ;

-- =====================================================
-- CREAR ÍNDICES PARA OPTIMIZAR RENDIMIENTO
-- =====================================================

-- Índices para appointments_appointment
CREATE INDEX IF NOT EXISTS idx_appointment_fecha ON appointments_appointment(fecha);
CREATE INDEX IF NOT EXISTS idx_appointment_doctor_fecha ON appointments_appointment(doctor_id, fecha);
CREATE INDEX IF NOT EXISTS idx_appointment_clinica_fecha ON appointments_appointment(clinica_id, fecha);
CREATE INDEX IF NOT EXISTS idx_appointment_estado ON appointments_appointment(estado);
CREATE INDEX IF NOT EXISTS idx_appointment_paciente ON appointments_appointment(paciente_id);

-- Índices para doctors_doctor
CREATE INDEX IF NOT EXISTS idx_doctor_clinica ON doctors_doctor(clinica_id);
CREATE INDEX IF NOT EXISTS idx_doctor_activo ON doctors_doctor(activo);
CREATE INDEX IF NOT EXISTS idx_doctor_usuario ON doctors_doctor(usuario_id);

-- Índices para patients_patient
CREATE INDEX IF NOT EXISTS idx_patient_clinica ON patients_patient(clinica_id);
CREATE INDEX IF NOT EXISTS idx_patient_dni ON patients_patient(dni);
CREATE INDEX IF NOT EXISTS idx_patient_prioridad ON patients_patient(prioridad);

-- Índices para clinicas_clinica
CREATE INDEX IF NOT EXISTS idx_clinica_codigo ON clinicas_clinica(codigo);
CREATE INDEX IF NOT EXISTS idx_clinica_activa ON clinicas_clinica(activa);

-- =====================================================
-- CREAR VISTAS PARA REPORTES FRECUENTES
-- =====================================================

-- Vista para estadísticas rápidas por clínica
CREATE OR REPLACE VIEW v_estadisticas_clinica AS
SELECT 
    c.id AS clinica_id,
    c.nombre AS clinica_nombre,
    c.codigo AS clinica_codigo,
    COUNT(DISTINCT d.id) AS total_doctores,
    COUNT(DISTINCT p.id) AS total_pacientes,
    COUNT(a.id) AS total_citas,
    COUNT(CASE WHEN a.estado = 'completada' THEN 1 END) AS citas_completadas,
    COUNT(CASE WHEN DATE(a.fecha) = CURDATE() THEN 1 END) AS citas_hoy,
    COUNT(CASE WHEN YEAR(a.fecha) = YEAR(CURDATE()) AND MONTH(a.fecha) = MONTH(CURDATE()) THEN 1 END) AS citas_mes_actual
FROM clinicas_clinica c
LEFT JOIN doctors_doctor d ON c.id = d.clinica_id AND d.activo = 1
LEFT JOIN patients_patient p ON c.id = p.clinica_id
LEFT JOIN appointments_appointment a ON c.id = a.clinica_id
WHERE c.activa = 1
GROUP BY c.id, c.nombre, c.codigo;

-- Vista para citas del día por doctor
CREATE OR REPLACE VIEW v_citas_hoy_doctor AS
SELECT 
    d.id AS doctor_id,
    CONCAT(d.nombre, ' ', d.apellidos) AS doctor_nombre,
    d.especialidad,
    c.nombre AS clinica_nombre,
    COUNT(a.id) AS citas_hoy,
    GROUP_CONCAT(
        CONCAT(TIME(a.fecha), ' - ', p.nombre, ' ', p.apellidos, ' (', a.estado, ')')
        ORDER BY a.fecha SEPARATOR '; '
    ) AS detalle_citas
FROM doctors_doctor d
INNER JOIN clinicas_clinica c ON d.clinica_id = c.id
LEFT JOIN appointments_appointment a ON d.id = a.doctor_id AND DATE(a.fecha) = CURDATE()
LEFT JOIN patients_patient p ON a.paciente_id = p.id
WHERE d.activo = 1
GROUP BY d.id, d.nombre, d.apellidos, d.especialidad, c.nombre;

-- =====================================================
-- PROCEDIMIENTO DE MANTENIMIENTO
-- =====================================================

DELIMITER //

CREATE PROCEDURE sp_mantenimiento_diario()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Actualizar citas vencidas a "no_asistio" si no se marcaron como completadas
    UPDATE appointments_appointment 
    SET estado = 'no_asistio'
    WHERE fecha < DATE_SUB(NOW(), INTERVAL 2 HOUR)
    AND estado = 'programada';
    
    -- Limpiar registros de reportes antiguos (más de 30 días)
    DELETE FROM reportes_reportegenerado 
    WHERE fecha_generacion < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    COMMIT;
    
    SELECT 'Mantenimiento completado exitosamente' AS resultado;
END //

DELIMITER ;

-- =====================================================
-- GRANTS Y PERMISOS (Opcional - ajustar según necesidades)
-- =====================================================

-- Crear usuario específico para la aplicación si no existe
-- CREATE USER IF NOT EXISTS 'medicitas_app'@'localhost' IDENTIFIED BY 'password_seguro';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON proyectodb.* TO 'medicitas_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE proyectodb.* TO 'medicitas_app'@'localhost';
-- FLUSH PRIVILEGES;

-- =====================================================
-- COMENTARIOS FINALES
-- =====================================================

/*
INSTRUCCIONES DE USO:

1. Ejecutar este script en la base de datos proyectodb
2. Los procedimientos están optimizados para el sistema multi-tenant
3. Incluyen validaciones y manejo de errores
4. Los índices mejoran el rendimiento de las consultas
5. Las vistas facilitan la generación de reportes

EJEMPLOS DE USO:

-- Obtener estadísticas de una clínica
CALL sp_obtener_estadisticas_clinica(1, '2024-01-01', '2024-12-31');

-- Reagendar una cita
CALL sp_reagendar_cita(123, '2024-11-15 10:30:00', 1, @resultado, @codigo);

-- Verificar disponibilidad de doctor
CALL sp_verificar_disponibilidad_doctor(5, '2024-11-15', '09:00:00', '17:00:00');

-- Obtener horarios disponibles
CALL sp_obtener_horarios_disponibles(5, '2024-11-15', 30);

-- Estadísticas del dashboard
CALL sp_estadisticas_dashboard(1, 1);
*/
