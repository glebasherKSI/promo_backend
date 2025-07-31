import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Сервис для отправки email-уведомлений"""
    
    def __init__(self):
        # Настройки SMTP из переменных окружения
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        
        # Проверяем наличие обязательных настроек
        if not self.smtp_username or not self.smtp_password:
            logger.warning("⚠️ SMTP настройки не найдены. Email уведомления отключены.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Email сервис инициализирован: {self.smtp_server}:{self.smtp_port}")
    
    def send_responsible_assignment_notification(
        self, 
        to_email: str, 
        responsible_name: str, 
        promo_name: str, 
        project: str,
        promo_type: str,
        start_date: str,
        end_date: str,
        assigned_by: str = "Система"
    ) -> bool:
        """
        Отправить уведомление о назначении ответственного
        
        Args:
            to_email: Email адрес получателя
            responsible_name: Имя ответственного
            promo_name: Название промо-акции
            project: Проект
            promo_type: Тип промо-акции
            start_date: Дата начала
            end_date: Дата окончания
            assigned_by: Кто назначил (по умолчанию "Система")
        
        Returns:
            bool: True если письмо отправлено успешно
        """
        if not self.enabled:
            logger.warning("Email сервис отключен - уведомление не отправлено")
            return False
        
        if not to_email:
            logger.warning("Email адрес не указан - уведомление не отправлено")
            return False
        
        try:
            # Формируем тему письма
            subject = f"Назначение ответственным за промо-акцию: {promo_name}"
            
            # Формируем текст письма
            body = f"""
Здравствуйте, {responsible_name}!

Вам назначена ответственность за промо-акцию в системе Promo Calendar.

Детали промо-акции:
• Название: {promo_name}
• Проект: {project}
• Тип: {promo_type}
• Дата начала: {start_date}
• Дата окончания: {end_date}


Пожалуйста, ознакомьтесь с деталями промо-акции и при необходимости свяжитесь с назначившим.

С уважением,
Система Promo Calendar
            """.strip()
            
            # Отправляем письмо
            success = self._send_email(to_email, subject, body)
            
            if success:
                logger.info(f"✅ Уведомление о назначении отправлено на {to_email}")
            else:
                logger.error(f"❌ Ошибка отправки уведомления на {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о назначении: {e}")
            return False
    
    def send_responsible_update_notification(
        self, 
        to_email: str, 
        responsible_name: str, 
        promo_name: str, 
        project: str,
        promo_type: str,
        start_date: str,
        end_date: str,
        updated_by: str = "Система"
    ) -> bool:
        """
        Отправить уведомление об обновлении ответственного
        
        Args:
            to_email: Email адрес получателя
            responsible_name: Имя ответственного
            promo_name: Название промо-акции
            project: Проект
            promo_type: Тип промо-акции
            start_date: Дата начала
            end_date: Дата окончания
            updated_by: Кто обновил (по умолчанию "Система")
        
        Returns:
            bool: True если письмо отправлено успешно
        """
        if not self.enabled:
            logger.warning("Email сервис отключен - уведомление не отправлено")
            return False
        
        if not to_email:
            logger.warning("Email адрес не указан - уведомление не отправлено")
            return False
        
        try:
            # Формируем тему письма
            subject = f"Обновление ответственности за промо-акцию: {promo_name}"
            
            # Формируем текст письма
            body = f"""
Здравствуйте, {responsible_name}!

Обновлена информация о промо-акции, за которую вы отвечаете.

Детали промо-акции:
• Название: {promo_name}
• Проект: {project}
• Тип: {promo_type}
• Дата начала: {start_date}
• Дата окончания: {end_date}
• Обновил: {updated_by}

Пожалуйста, ознакомьтесь с обновленными деталями промо-акции.

С уважением,
Система Promo Calendar
            """.strip()
            
            # Отправляем письмо
            success = self._send_email(to_email, subject, body)
            
            if success:
                logger.info(f"✅ Уведомление об обновлении отправлено на {to_email}")
            else:
                logger.error(f"❌ Ошибка отправки уведомления на {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления об обновлении: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Отправить email
        
        Args:
            to_email: Email адрес получателя
            subject: Тема письма
            body: Текст письма
        
        Returns:
            bool: True если письмо отправлено успешно
        """
        try:
            # Создаем объект сообщения
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Добавляем текст письма
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Подключаемся к SMTP серверу
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Включаем шифрование
                server.login(self.smtp_username, self.smtp_password)
                
                # Отправляем письмо
                text = msg.as_string()
                server.sendmail(self.from_email, to_email, text)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки email на {to_email}: {e}")
            return False

# Глобальный экземпляр сервиса
email_service = EmailService() 