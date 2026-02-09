"""
System Monitoring Service | 系统监控服务
Monitors system resources, AI performance, and provides early warning.

Features:
- CPU/Memory/Disk monitoring
- Docker container status tracking
- Database performance metrics
- AI diagnosis anomaly detection
- Alert generation

支持：
- CPU/内存/磁盘监控
- Docker容器状态追踪
- 数据库性能指标
- AI诊断异常检测
- 告警生成
"""

import logging
import psutil
import docker
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import SystemResourceLog, AIDiagnosisLog, AdminOperationLog, User
import uuid

logger = logging.getLogger(__name__)


class SystemMonitoringService:
    """
    System Monitoring Service / 系统监控服务
    
    Collects and analyzes system metrics for admin dashboard.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        try:
            self.docker_client = docker.from_env()
        except:
            self.docker_client = None
            logger.warning("Docker client not available")
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect current system metrics / 收集当前系统指标
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {},
            "memory": {},
            "disk": {},
            "containers": {},
            "database": {}
        }
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            metrics["cpu"] = {
                "percent": cpu_percent,
                "count": cpu_count,
                "alert_level": self._get_alert_level(cpu_percent, "cpu")
            }
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics["memory"] = {
                "percent": memory.percent,
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "alert_level": self._get_alert_level(memory.percent, "memory")
            }
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics["disk"] = {
                "percent": round(disk_percent, 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "alert_level": self._get_alert_level(disk_percent, "disk")
            }
            
            # Docker container metrics
            if self.docker_client:
                try:
                    containers = self.docker_client.containers.list()
                    container_metrics = {}
                    for container in containers:
                        stats = container.stats(stream=False)
                        container_metrics[container.name] = {
                            "status": container.status,
                            "cpu_percent": self._calculate_container_cpu_percent(stats),
                            "memory_usage_mb": round(stats.get('memory_stats', {}).get('usage', 0) / (1024**2), 2)
                        }
                    metrics["containers"] = container_metrics
                except Exception as e:
                    logger.warning(f"Failed to get container metrics: {e}")
            
            # Database metrics
            try:
                # Query count
                result = await self.db.execute(select(func.count()).select_from(User))
                user_count = result.scalar()
                
                metrics["database"] = {
                    "user_count": user_count,
                    "alert_level": "info"
                }
            except Exception as e:
                logger.warning(f"Failed to get database metrics: {e}")
            
            # Determine overall alert level
            alert_levels = [
                metrics["cpu"].get("alert_level", "info"),
                metrics["memory"].get("alert_level", "info"),
                metrics["disk"].get("alert_level", "info")
            ]
            
            if "critical" in alert_levels:
                metrics["overall_alert"] = "critical"
                metrics["alert_message"] = "系统资源严重不足，请立即处理"
            elif "warning" in alert_levels:
                metrics["overall_alert"] = "warning"
                metrics["alert_message"] = "系统资源使用较高，请关注"
            else:
                metrics["overall_alert"] = "info"
                metrics["alert_message"] = None
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _get_alert_level(self, percent: float, resource_type: str) -> str:
        """Determine alert level based on percentage / 根据百分比确定告警级别"""
        if resource_type == "cpu":
            if percent > 90:
                return "critical"
            elif percent > 70:
                return "warning"
            return "info"
        elif resource_type == "memory":
            if percent > 90:
                return "critical"
            elif percent > 80:
                return "warning"
            return "info"
        elif resource_type == "disk":
            if percent > 95:
                return "critical"
            elif percent > 85:
                return "warning"
            return "info"
        return "info"
    
    def _calculate_container_cpu_percent(self, stats: dict) -> float:
        """Calculate container CPU percentage / 计算容器CPU使用率"""
        try:
            cpu_delta = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) - \
                       stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
            system_delta = stats.get('cpu_stats', {}).get('system_cpu_usage', 0) - \
                          stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
            
            if system_delta > 0 and cpu_delta > 0:
                return round((cpu_delta / system_delta) * 100, 2)
        except:
            pass
        return 0.0
    
    async def log_system_metrics(self) -> SystemResourceLog:
        """Log system metrics to database / 记录系统指标到数据库"""
        metrics = await self.collect_system_metrics()
        
        if "error" in metrics:
            return None
        
        log = SystemResourceLog(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            cpu_percent=metrics.get("cpu", {}).get("percent"),
            memory_percent=metrics.get("memory", {}).get("percent"),
            disk_percent=metrics.get("disk", {}).get("percent"),
            container_status=metrics.get("containers"),
            db_connections=None,  # Would need actual connection pool info
            db_query_time_avg=None,
            alert_level=metrics.get("overall_alert", "info"),
            alert_message=metrics.get("alert_message")
        )
        
        self.db.add(log)
        await self.db.commit()
        
        return log
    
    async def get_recent_metrics(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent system metrics / 获取最近的系统指标"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(SystemResourceLog).where(
            SystemResourceLog.timestamp >= since
        ).order_by(SystemResourceLog.timestamp.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        
        return [
            {
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "cpu_percent": log.cpu_percent,
                "memory_percent": log.memory_percent,
                "disk_percent": log.disk_percent,
                "alert_level": log.alert_level,
                "alert_message": log.alert_message
            }
            for log in logs
        ]
    
    async def get_ai_diagnosis_statistics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get AI diagnosis statistics / 获取AI诊断统计"""
        since = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(AIDiagnosisLog).where(
            AIDiagnosisLog.timestamp >= since
        )
        
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        
        total_requests = len(logs)
        successful = len([l for l in logs if l.status == 'success'])
        failed = len([l for l in logs if l.status == 'error'])
        timeouts = len([l for l in logs if l.status == 'timeout'])
        anomalies = len([l for l in logs if l.is_anomaly])
        
        # Average latency
        latencies = [l.request_duration_ms for l in logs if l.request_duration_ms]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Status breakdown
        status_breakdown = {}
        for log in logs:
            status = log.status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "timeouts": timeouts,
            "anomalies": anomalies,
            "success_rate": round(successful / total_requests * 100, 2) if total_requests > 0 else 0,
            "average_latency_ms": round(avg_latency, 2),
            "status_breakdown": status_breakdown
        }
    
    async def detect_anomalies(
        self,
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Detect AI diagnosis anomalies / 检测AI诊断异常"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(AIDiagnosisLog).where(
            AIDiagnosisLog.timestamp >= since,
            AIDiagnosisLog.is_anomaly == True
        )
        
        result = await self.db.execute(stmt)
        anomalies = result.scalars().all()
        
        return [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "user_id": str(log.user_id) if log.user_id else None,
                "request_type": log.request_type,
                "status": log.status,
                "duration_ms": log.request_duration_ms,
                "error_message": log.error_message,
                "anomaly_reason": log.anomaly_reason
            }
            for log in anomalies
        ]


class AIDiagnosisLogger:
    """
    AI Diagnosis Logger / AI诊断日志记录器
    
    Logs AI diagnosis requests for monitoring and analysis.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_diagnosis(
        self,
        user_id: uuid.UUID,
        request_type: str,
        ai_model_id: str,
        ai_api_url: str,
        duration_ms: int,
        tokens_input: int,
        tokens_output: int,
        status: str,
        error_message: str = None
    ) -> AIDiagnosisLog:
        """Log an AI diagnosis request / 记录AI诊断请求"""
        
        # Detect anomalies
        is_anomaly = False
        anomaly_reason = None
        
        if status == 'timeout':
            is_anomaly = True
            anomaly_reason = "Request timeout"
        elif status == 'error':
            is_anomaly = True
            anomaly_reason = f"API error: {error_message[:100]}" if error_message else "Unknown error"
        elif duration_ms > 30000:  # > 30 seconds
            is_anomaly = True
            anomaly_reason = f"High latency: {duration_ms}ms"
        
        log = AIDiagnosisLog(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            request_type=request_type,
            ai_model_id=ai_model_id,
            ai_api_url=ai_api_url,
            request_duration_ms=duration_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            status=status,
            error_message=error_message,
            is_anomaly=is_anomaly,
            anomaly_reason=anomaly_reason
        )
        
        self.db.add(log)
        await self.db.commit()
        
        if is_anomaly:
            logger.warning(f"AI diagnosis anomaly detected: {anomaly_reason}")
        
        return log


class AdminOperationLogger:
    """
    Admin Operation Logger / 管理员操作日志记录器
    
    Logs admin operations for audit trail.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_operation(
        self,
        admin_id: uuid.UUID,
        operation_type: str,
        operation_details: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> AdminOperationLog:
        """Log an admin operation / 记录管理员操作"""
        
        log = AdminOperationLog(
            id=uuid.uuid4(),
            admin_id=admin_id,
            timestamp=datetime.utcnow(),
            operation_type=operation_type,
            operation_details=operation_details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        await self.db.commit()
        
        logger.info(f"Admin operation logged: {operation_type} by {admin_id}")
        
        return log
    
    async def get_recent_operations(
        self,
        admin_id: uuid.UUID = None,
        operation_type: str = None,
        days: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent admin operations / 获取最近的管理员操作"""
        since = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(AdminOperationLog).where(
            AdminOperationLog.timestamp >= since
        )
        
        if admin_id:
            stmt = stmt.where(AdminOperationLog.admin_id == admin_id)
        
        if operation_type:
            stmt = stmt.where(AdminOperationLog.operation_type == operation_type)
        
        stmt = stmt.order_by(AdminOperationLog.timestamp.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        
        return [
            {
                "id": str(log.id),
                "admin_id": str(log.admin_id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "operation_type": log.operation_type,
                "operation_details": log.operation_details,
                "ip_address": str(log.ip_address) if log.ip_address else None
            }
            for log in logs
        ]


# Global service instances
def get_monitoring_service(db: AsyncSession) -> SystemMonitoringService:
    return SystemMonitoringService(db)


def get_ai_logger(db: AsyncSession) -> AIDiagnosisLogger:
    return AIDiagnosisLogger(db)


def get_admin_logger(db: AsyncSession) -> AdminOperationLogger:
    return AdminOperationLogger(db)
