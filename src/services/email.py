import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailService:
    """Email notification service."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        logger: logging.Logger | None = None
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.logger = logger or logging.getLogger(__name__)

    def send_email(
        self,
        to_emails: list[str],
        subject: str,
        body: str,
        retries: int = 3
    ) -> bool:

        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        for attempt in range(retries):
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.sendmail(self.from_email, to_emails, msg.as_string())

                self.logger.info(f"Email enviado a {to_emails}")
                return True

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} - Error: {e}")
                if attempt < retries - 1:
                    time.sleep(5)

        return False

    def send_price_alert(
        self,
        old_price: float,
        new_price: float,
        flight_data: dict,
        to_emails: list[str]
    ) -> bool:
        drop = old_price - new_price

        subject = f"PRECIO BAJO - Vuelo {flight_data.get('origin')} -> {flight_data.get('destination')}"

        body = f"""
        <h2>Precio Bajo!</h2>
        <p><b>Origen:</b> {flight_data.get('origin')}</p>
        <p><b>Destino:</b> {flight_data.get('destination')}</p>
        <p><b>Precio anterior:</b> ${old_price:,.0f}</p>
        <p><b>Precio actual:</b> ${new_price:,.0f}</p>
        <p><b>Ahorro:</b> ${drop:,.0f}</p>
        <p><b>Aerolínea:</b> {flight_data.get('airline')}</p>
        <p><b>Fecha:</b> {flight_data.get('date')}</p>
        <p><b>Booking ID:</b> {flight_data.get('booking_link')}</p>
        """

        return self.send_email(to_emails, subject, body)

    def send_price_summary(
        self,
        flights: list,
        date: str,
        to_emails: list[str]
    ) -> bool:

        flights.sort(key=lambda x: x.price)

        subject = f" Mejores Precios - Santa Marta {date}"

        body = "<h2>Mejores Precios - Santa Marta</h2>"
        body += f"<p>Fecha: {date}</p>"

        for i, flight in enumerate(flights[:3], 1):
            body += f"""
            <hr>
            <h3>{i}. {flight.origin} -> {flight.destination}</h3>
            <p><b>Precio:</b> ${flight.price:,.0f} {flight.currency}</p>
            <p><b>Aerolínea:</b> {flight.airline}</p>
            <p><b>Booking ID:</b> {flight.booking_link}</p>
            """

        return self.send_email(to_emails, subject, body)
