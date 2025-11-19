"""
Audit Logger - Tüm işlemleri kayıt altına alma sistemi
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import os


class AuditLogger:
    """
    Comprehensive audit logging system
    - Tüm trade işlemleri
    - API istekleri
    - Sistem olayları
    - Hata kayıtları
    """

    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Farklı log dosyaları
        self.trade_log = self._setup_logger("trades", "trades.log")
        self.api_log = self._setup_logger("api", "api.log")
        self.system_log = self._setup_logger("system", "system.log")
        self.error_log = self._setup_logger("errors", "errors.log")

    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        """Setup individual logger"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(
            self.log_dir / filename,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def log_trade(
        self,
        action: str,
        symbol: str,
        quantity: float,
        price: float,
        order_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log trade işlemleri"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "order_type": order_type,
            "total_value": quantity * price,
            "metadata": metadata or {}
        }

        self.trade_log.info(json.dumps(log_entry, ensure_ascii=False))

    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        response_time: float,
        client_ip: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log API istekleri"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "client_ip": client_ip,
            "metadata": metadata or {}
        }

        self.api_log.info(json.dumps(log_entry, ensure_ascii=False))

    def log_system_event(
        self,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log sistem olayları"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {}
        }

        self.system_log.info(json.dumps(log_entry, ensure_ascii=False))

    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log hatalar"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "metadata": metadata or {}
        }

        self.error_log.error(json.dumps(log_entry, ensure_ascii=False))

    def get_recent_trades(self, limit: int = 100) -> list:
        """Son trade'leri getir"""
        return self._read_log_file("trades.log", limit)

    def get_recent_api_calls(self, limit: int = 100) -> list:
        """Son API çağrılarını getir"""
        return self._read_log_file("api.log", limit)

    def get_recent_errors(self, limit: int = 100) -> list:
        """Son hataları getir"""
        return self._read_log_file("errors.log", limit)

    def _read_log_file(self, filename: str, limit: int) -> list:
        """Log dosyasından son N satırı oku"""
        log_file = self.log_dir / filename

        if not log_file.exists():
            return []

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Son N satırı al ve parse et
            recent_lines = lines[-limit:]
            parsed_logs = []

            for line in recent_lines:
                try:
                    # Log format: timestamp | level | json_data
                    parts = line.split(' | ', 2)
                    if len(parts) >= 3:
                        json_data = json.loads(parts[2])
                        parsed_logs.append(json_data)
                except:
                    continue

            return parsed_logs
        except Exception as e:
            self.error_log.error(f"Failed to read log file {filename}: {e}")
            return []


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


if __name__ == "__main__":
    # Test the audit logger
    logger = AuditLogger()

    # Test trade log
    logger.log_trade(
        action="BUY",
        symbol="THYAO.IS",
        quantity=100,
        price=45.50,
        order_type="MARKET",
        metadata={"strategy": "combined", "signal_strength": 0.85}
    )

    # Test API log
    logger.log_api_request(
        method="GET",
        endpoint="/api/portfolio",
        status_code=200,
        response_time=0.045,
        client_ip="127.0.0.1"
    )

    # Test system event
    logger.log_system_event(
        event_type="AUTO_TRADING_STARTED",
        description="Auto trading started with combined strategy",
        metadata={"symbols": ["THYAO.IS", "ASELS.IS"], "interval": 60}
    )

    # Test error log
    logger.log_error(
        error_type="DataFetchError",
        error_message="Failed to fetch market data",
        stack_trace="...",
        metadata={"symbol": "INVALID"}
    )

    print("✓ Audit logger test completed")
    print(f"Log files created in: {logger.log_dir}")
