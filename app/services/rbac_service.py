"""
RBAC权限管理服务
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload

from app.models import Role, Permission, UserRole, RolePermission, User
from app.core.exceptions import NotFoundError, ConflictError, ValidationError


class RBACService:
    """RBAC权限管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 角色管理 ====================
    
    async def create_role(
        self,
        user_pool_id: int,
        role_name: str,
        role_code: str,
        description: Optional[str] = None,
        is_system: bool = False
    ) -> Role:
        """创建角色"""
        # 检查角色代码唯一性
        existing = await self.db.execute(
            select(Role).where(
                and_(
                    Role.user_pool_id == user_pool_id,
                    Role.role_code == role_code
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("角色代码已存在")
        
        role = Role(
            user_pool_id=user_pool_id,
            role_name=role_name,
            role_code=role_code,
            description=description,
            is_system=is_system
        )
        
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        
        return role
    
    async def update_role(
        self,
        role_id: int,
        role_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Role:
        """更新角色"""
        role = await self.get_role_by_id(role_id)
        
        if role.is_system:
            raise ValidationError("系统角色不能修改")
        
        if role_name is not None:
            role.role_name = role_name
        
        if description is not None:
            role.description = description
        
        await self.db.commit()
        await self.db.refresh(role)
        
        return role
    
    async def get_role_by_id(self, role_id: int) -> Role:
        """根据ID获取角色"""
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundError("角色不存在")
        
        return role
    
    async def get_role_by_code(self, user_pool_id: int, role_code: str) -> Optional[Role]:
        """根据角色代码获取角色"""
        result = await self.db.execute(
            select(Role).where(
                and_(
                    Role.user_pool_id == user_pool_id,
                    Role.role_code == role_code
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_roles(
        self,
        user_pool_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Role], int]:
        """获取角色列表"""
        query = select(Role).where(Role.user_pool_id == user_pool_id)
        
        # 计算总数
        count_query = select(func.count(Role.id)).where(Role.user_pool_id == user_pool_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.offset((page - 1) * per_page).limit(per_page)
        query = query.order_by(Role.created_at.desc())
        
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        return list(roles), total
    
    async def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        role = await self.get_role_by_id(role_id)
        
        if role.is_system:
            raise ValidationError("系统角色不能删除")
        
        # 检查是否有用户使用此角色
        user_role_result = await self.db.execute(
            select(func.count(UserRole.user_id)).where(UserRole.role_id == role_id)
        )
        user_count = user_role_result.scalar()
        
        if user_count > 0:
            raise ValidationError("角色正在使用中，不能删除")
        
        # 删除角色权限关联
        await self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        
        # 删除角色
        await self.db.delete(role)
        await self.db.commit()
        
        return True
    
    # ==================== 权限管理 ====================
    
    async def create_permission(
        self,
        user_pool_id: int,
        permission_name: str,
        permission_code: str,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """创建权限"""
        # 检查权限代码唯一性
        existing = await self.db.execute(
            select(Permission).where(
                and_(
                    Permission.user_pool_id == user_pool_id,
                    Permission.permission_code == permission_code
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("权限代码已存在")
        
        permission = Permission(
            user_pool_id=user_pool_id,
            permission_name=permission_name,
            permission_code=permission_code,
            resource=resource,
            action=action,
            description=description
        )
        
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        
        return permission
    
    async def update_permission(
        self,
        permission_id: int,
        permission_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Permission:
        """更新权限"""
        permission = await self.get_permission_by_id(permission_id)
        
        if permission_name is not None:
            permission.permission_name = permission_name
        
        if description is not None:
            permission.description = description
        
        await self.db.commit()
        await self.db.refresh(permission)
        
        return permission
    
    async def get_permission_by_id(self, permission_id: int) -> Permission:
        """根据ID获取权限"""
        result = await self.db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise NotFoundError("权限不存在")
        
        return permission
    
    async def list_permissions(
        self,
        user_pool_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Permission], int]:
        """获取权限列表"""
        query = select(Permission).where(Permission.user_pool_id == user_pool_id)
        
        # 计算总数
        count_query = select(func.count(Permission.id)).where(Permission.user_pool_id == user_pool_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.offset((page - 1) * per_page).limit(per_page)
        query = query.order_by(Permission.created_at.desc())
        
        result = await self.db.execute(query)
        permissions = result.scalars().all()
        
        return list(permissions), total
    
    async def delete_permission(self, permission_id: int) -> bool:
        """删除权限"""
        permission = await self.get_permission_by_id(permission_id)
        
        # 删除角色权限关联
        await self.db.execute(
            delete(RolePermission).where(RolePermission.permission_id == permission_id)
        )
        
        # 删除权限
        await self.db.delete(permission)
        await self.db.commit()
        
        return True
    
    # ==================== 角色权限关联 ====================
    
    async def assign_permissions_to_role(
        self,
        role_id: int,
        permission_ids: List[int]
    ) -> bool:
        """为角色分配权限"""
        role = await self.get_role_by_id(role_id)
        
        # 验证权限存在且属于同一用户池
        for permission_id in permission_ids:
            permission = await self.get_permission_by_id(permission_id)
            if permission.user_pool_id != role.user_pool_id:
                raise ValidationError("权限不属于同一用户池")
        
        # 删除现有权限关联
        await self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        
        # 添加新的权限关联
        for permission_id in permission_ids:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id
            )
            self.db.add(role_permission)
        
        await self.db.commit()
        return True
    
    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """获取角色的权限列表"""
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        return list(result.scalars().all())
    
    # ==================== 用户角色管理 ====================
    
    async def assign_roles_to_user(
        self,
        user_id: int,
        role_ids: List[int],
        granted_by: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """为用户分配角色"""
        # 验证用户存在
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("用户不存在")
        
        # 验证角色存在且属于同一用户池
        for role_id in role_ids:
            role = await self.get_role_by_id(role_id)
            if role.user_pool_id != user.user_pool_id:
                raise ValidationError("角色不属于同一用户池")
        
        # 删除用户现有角色
        await self.db.execute(
            delete(UserRole).where(UserRole.user_id == user_id)
        )
        
        # 添加新的角色关联
        for role_id in role_ids:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                granted_by=granted_by,
                granted_at=datetime.now(UTC),
                expires_at=expires_at
            )
            self.db.add(user_role)
        
        await self.db.commit()
        return True
    
    async def revoke_roles_from_user(
        self,
        user_id: int,
        role_ids: List[int]
    ) -> bool:
        """撤销用户角色"""
        await self.db.execute(
            delete(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id.in_(role_ids)
                )
            )
        )
        await self.db.commit()
        return True
    
    async def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的角色列表"""
        result = await self.db.execute(
            select(Role, UserRole)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        
        user_roles = []
        for role, user_role in result.all():
            user_roles.append({
                "user_id": user_role.user_id,
                "role_id": role.id,
                "role_name": role.role_name,
                "role_code": role.role_code,
                "granted_by": user_role.granted_by,
                "granted_at": user_role.granted_at,
                "expires_at": user_role.expires_at
            })
        
        return user_roles
    
    async def get_user_permissions(self, user_id: int) -> List[Permission]:
        """获取用户的所有权限"""
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.now(UTC)
                    )
                )
            )
            .distinct()
        )
        return list(result.scalars().all())
    
    async def check_user_permission(
        self,
        user_id: int,
        resource: str,
        action: str
    ) -> bool:
        """检查用户是否有特定权限"""
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Permission.resource == resource,
                    Permission.action == action,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.now(UTC)
                    )
                )
            )
        )
        permission = result.scalar_one_or_none()
        return permission is not None
    
    # ==================== 批量操作 ====================
    
    async def init_default_roles_and_permissions(self, user_pool_id: int) -> bool:
        """初始化默认角色和权限"""
        # 创建默认角色
        admin_role = await self.create_role(
            user_pool_id=user_pool_id,
            role_name="管理员",
            role_code="admin",
            description="系统管理员，拥有所有权限",
            is_system=True
        )
        
        user_role = await self.create_role(
            user_pool_id=user_pool_id,
            role_name="普通用户",
            role_code="user",
            description="普通用户，拥有基本权限",
            is_system=True
        )
        
        # 创建默认权限
        permissions = [
            ("用户管理", "user:read", "user", "read", "查看用户信息"),
            ("用户创建", "user:write", "user", "write", "创建和编辑用户"),
            ("用户删除", "user:delete", "user", "delete", "删除用户"),
            ("角色管理", "role:read", "role", "read", "查看角色信息"),
            ("角色编辑", "role:write", "role", "write", "创建和编辑角色"),
            ("权限管理", "permission:read", "permission", "read", "查看权限信息"),
            ("权限编辑", "permission:write", "permission", "write", "创建和编辑权限"),
        ]
        
        permission_objects = []
        for name, code, resource, action, desc in permissions:
            permission = await self.create_permission(
                user_pool_id=user_pool_id,
                permission_name=name,
                permission_code=code,
                resource=resource,
                action=action,
                description=desc
            )
            permission_objects.append(permission)
        
        # 为管理员角色分配所有权限
        await self.assign_permissions_to_role(
            role_id=admin_role.id,
            permission_ids=[p.id for p in permission_objects]
        )
        
        # 为普通用户角色分配基本读取权限
        basic_permissions = [p.id for p in permission_objects if ":read" in p.permission_code]
        await self.assign_permissions_to_role(
            role_id=user_role.id,
            permission_ids=basic_permissions
        )
        
        return True
