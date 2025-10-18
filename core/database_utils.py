"""
Database utilities for MySQL stored procedures and advanced queries
"""
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MySQLStoredProcedures:
    """
    Class to manage MySQL stored procedures for MediCitas Pro
    """
    
    @staticmethod
    def create_all_procedures():
        """Create all stored procedures"""
        procedures = [
            MySQLStoredProcedures.create_filter_appointments_by_date_sp(),
            MySQLStoredProcedures.create_doctor_statistics_sp(),
            MySQLStoredProcedures.create_patient_statistics_sp(),
            MySQLStoredProcedures.create_appointment_analytics_sp(),
            MySQLStoredProcedures.create_filter_patients_sp(),
        ]
        
        with connection.cursor() as cursor:
            for procedure in procedures:
                try:
                    cursor.execute(procedure)
                    logger.info(f"Stored procedure created successfully")
                except Exception as e:
                    logger.error(f"Error creating stored procedure: {e}")
    
    @staticmethod
    def create_filter_appointments_by_date_sp():
        """Create stored procedure to filter appointments by date range"""
        return """
        DROP PROCEDURE IF EXISTS FilterAppointmentsByDate;
        
        CREATE PROCEDURE FilterAppointmentsByDate(
            IN doctor_id INT,
            IN start_date DATE,
            IN end_date DATE,
            IN priority_filter VARCHAR(1)
        )
        BEGIN
            SELECT 
                a.id,
                a.fecha,
                a.motivo,
                a.observaciones,
                p.nombre as patient_name,
                p.apellidos as patient_lastname,
                p.dni as patient_dni,
                p.prioridad as patient_priority,
                d.nombre as doctor_name,
                d.apellidos as doctor_lastname,
                d.especialidad as doctor_specialty
            FROM appointments_appointment a
            INNER JOIN patients_patient p ON a.paciente_id = p.id
            INNER JOIN doctors_doctor d ON a.doctor_id = d.id
            WHERE a.doctor_id = doctor_id
                AND DATE(a.fecha) BETWEEN start_date AND end_date
                AND (priority_filter IS NULL OR priority_filter = '' OR p.prioridad = priority_filter)
            ORDER BY a.fecha ASC;
        END;
        """
    
    @staticmethod
    def create_doctor_statistics_sp():
        """Create stored procedure for doctor statistics"""
        return """
        DROP PROCEDURE IF EXISTS GetDoctorStatistics;
        
        CREATE PROCEDURE GetDoctorStatistics(
            IN doctor_id INT
        )
        BEGIN
            SELECT 
                -- Basic counts
                COUNT(DISTINCT a.id) as total_appointments,
                COUNT(DISTINCT CASE WHEN DATE(a.fecha) = CURDATE() THEN a.id END) as today_appointments,
                COUNT(DISTINCT CASE WHEN YEARWEEK(a.fecha) = YEARWEEK(CURDATE()) THEN a.id END) as week_appointments,
                COUNT(DISTINCT CASE WHEN YEAR(a.fecha) = YEAR(CURDATE()) AND MONTH(a.fecha) = MONTH(CURDATE()) THEN a.id END) as month_appointments,
                COUNT(DISTINCT p.id) as total_patients,
                
                -- Upcoming appointments
                COUNT(DISTINCT CASE WHEN a.fecha > NOW() THEN a.id END) as upcoming_appointments,
                
                -- Priority breakdown
                COUNT(DISTINCT CASE WHEN p.prioridad = 'U' THEN a.id END) as urgent_appointments,
                COUNT(DISTINCT CASE WHEN p.prioridad = 'A' THEN a.id END) as high_priority_appointments,
                COUNT(DISTINCT CASE WHEN p.prioridad = 'M' THEN a.id END) as medium_priority_appointments,
                COUNT(DISTINCT CASE WHEN p.prioridad = 'B' THEN a.id END) as low_priority_appointments,
                
                -- Average appointments per day
                ROUND(COUNT(DISTINCT a.id) / GREATEST(DATEDIFF(CURDATE(), MIN(DATE(a.fecha))), 1), 2) as avg_appointments_per_day
                
            FROM appointments_appointment a
            INNER JOIN patients_patient p ON a.paciente_id = p.id
            WHERE a.doctor_id = doctor_id;
        END;
        """
    
    @staticmethod
    def create_patient_statistics_sp():
        """Create stored procedure for patient statistics by doctor"""
        return """
        DROP PROCEDURE IF EXISTS GetPatientStatistics;
        
        CREATE PROCEDURE GetPatientStatistics(
            IN doctor_id INT
        )
        BEGIN
            SELECT 
                p.id,
                p.nombre,
                p.apellidos,
                p.dni,
                p.prioridad,
                p.fecha_nacimiento,
                COUNT(a.id) as total_appointments,
                MAX(a.fecha) as last_appointment,
                MIN(a.fecha) as first_appointment,
                COUNT(CASE WHEN a.fecha > NOW() THEN 1 END) as upcoming_appointments,
                COUNT(CASE WHEN a.fecha <= NOW() THEN 1 END) as completed_appointments,
                TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURDATE()) as age
            FROM patients_patient p
            LEFT JOIN appointments_appointment a ON p.id = a.paciente_id AND a.doctor_id = doctor_id
            WHERE EXISTS (
                SELECT 1 FROM appointments_appointment a2 
                WHERE a2.paciente_id = p.id AND a2.doctor_id = doctor_id
            )
            GROUP BY p.id, p.nombre, p.apellidos, p.dni, p.prioridad, p.fecha_nacimiento
            ORDER BY total_appointments DESC, p.apellidos, p.nombre;
        END;
        """
    
    @staticmethod
    def create_appointment_analytics_sp():
        """Create stored procedure for appointment analytics"""
        return """
        DROP PROCEDURE IF EXISTS GetAppointmentAnalytics;
        
        CREATE PROCEDURE GetAppointmentAnalytics(
            IN start_date DATE,
            IN end_date DATE
        )
        BEGIN
            SELECT 
                -- Doctor performance
                d.id as doctor_id,
                d.nombre as doctor_name,
                d.apellidos as doctor_lastname,
                d.especialidad,
                COUNT(a.id) as total_appointments,
                COUNT(DISTINCT a.paciente_id) as unique_patients,
                
                -- Appointment status
                COUNT(CASE WHEN a.fecha > NOW() THEN 1 END) as scheduled_appointments,
                COUNT(CASE WHEN a.fecha <= NOW() THEN 1 END) as completed_appointments,
                
                -- Priority distribution
                COUNT(CASE WHEN p.prioridad = 'U' THEN 1 END) as urgent_count,
                COUNT(CASE WHEN p.prioridad = 'A' THEN 1 END) as high_priority_count,
                COUNT(CASE WHEN p.prioridad = 'M' THEN 1 END) as medium_priority_count,
                COUNT(CASE WHEN p.prioridad = 'B' THEN 1 END) as low_priority_count,
                
                -- Percentages
                ROUND((COUNT(a.id) * 100.0 / (SELECT COUNT(*) FROM appointments_appointment WHERE DATE(fecha) BETWEEN start_date AND end_date)), 2) as percentage_of_total,
                ROUND(AVG(TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURDATE())), 1) as avg_patient_age
                
            FROM doctors_doctor d
            LEFT JOIN appointments_appointment a ON d.id = a.doctor_id 
                AND DATE(a.fecha) BETWEEN start_date AND end_date
            LEFT JOIN patients_patient p ON a.paciente_id = p.id
            GROUP BY d.id, d.nombre, d.apellidos, d.especialidad
            HAVING total_appointments > 0
            ORDER BY total_appointments DESC;
        END;
        """
    
    @staticmethod
    def create_filter_patients_sp():
        """Create stored procedure to filter patients with advanced search"""
        return """
        DROP PROCEDURE IF EXISTS FilterPatients;
        
        CREATE PROCEDURE FilterPatients(
            IN doctor_id INT,
            IN search_term VARCHAR(255),
            IN priority_filter VARCHAR(1),
            IN age_min INT,
            IN age_max INT,
            IN limit_count INT,
            IN offset_count INT
        )
        BEGIN
            SELECT 
                p.id,
                p.nombre,
                p.apellidos,
                p.dni,
                p.prioridad,
                p.fecha_nacimiento,
                p.historial_medico_basico,
                p.informacion_contacto,
                COUNT(a.id) as total_appointments,
                MAX(a.fecha) as last_appointment,
                TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURDATE()) as age,
                CASE 
                    WHEN p.prioridad = 'U' THEN 'Urgente'
                    WHEN p.prioridad = 'A' THEN 'Alta'
                    WHEN p.prioridad = 'M' THEN 'Media'
                    WHEN p.prioridad = 'B' THEN 'Baja'
                    ELSE 'Sin definir'
                END as priority_display
            FROM patients_patient p
            LEFT JOIN appointments_appointment a ON p.id = a.paciente_id AND a.doctor_id = doctor_id
            WHERE EXISTS (
                SELECT 1 FROM appointments_appointment a2 
                WHERE a2.paciente_id = p.id AND a2.doctor_id = doctor_id
            )
            AND (
                search_term IS NULL OR search_term = '' OR
                p.nombre LIKE CONCAT('%', search_term, '%') OR
                p.apellidos LIKE CONCAT('%', search_term, '%') OR
                p.dni LIKE CONCAT('%', search_term, '%') OR
                p.informacion_contacto LIKE CONCAT('%', search_term, '%')
            )
            AND (priority_filter IS NULL OR priority_filter = '' OR p.prioridad = priority_filter)
            AND (age_min IS NULL OR TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURDATE()) >= age_min)
            AND (age_max IS NULL OR TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURDATE()) <= age_max)
            GROUP BY p.id, p.nombre, p.apellidos, p.dni, p.prioridad, p.fecha_nacimiento, p.historial_medico_basico, p.informacion_contacto
            ORDER BY p.apellidos, p.nombre
            LIMIT limit_count OFFSET offset_count;
        END;
        """

    @staticmethod
    def call_filter_appointments_by_date(doctor_id, start_date, end_date, priority_filter=None):
        """Call the FilterAppointmentsByDate stored procedure"""
        with connection.cursor() as cursor:
            cursor.callproc('FilterAppointmentsByDate', [doctor_id, start_date, end_date, priority_filter])
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
    
    @staticmethod
    def call_doctor_statistics(doctor_id):
        """Call the GetDoctorStatistics stored procedure"""
        with connection.cursor() as cursor:
            cursor.callproc('GetDoctorStatistics', [doctor_id])
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchone()
            return dict(zip(columns, result)) if result else {}
    
    @staticmethod
    def call_patient_statistics(doctor_id):
        """Call the GetPatientStatistics stored procedure"""
        with connection.cursor() as cursor:
            cursor.callproc('GetPatientStatistics', [doctor_id])
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
    
    @staticmethod
    def call_appointment_analytics(start_date, end_date):
        """Call the GetAppointmentAnalytics stored procedure"""
        with connection.cursor() as cursor:
            cursor.callproc('GetAppointmentAnalytics', [start_date, end_date])
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
    
    @staticmethod
    def call_filter_patients(doctor_id, search_term=None, priority_filter=None, age_min=None, age_max=None, limit_count=20, offset_count=0):
        """Call the FilterPatients stored procedure"""
        with connection.cursor() as cursor:
            cursor.callproc('FilterPatients', [doctor_id, search_term, priority_filter, age_min, age_max, limit_count, offset_count])
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
