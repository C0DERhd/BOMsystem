from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional, Set, Tuple
import re

from sqlalchemy import or_

from app import db
from app.models.bom import BOM, BOMItem, BOMVersion, format_bom_version
from app.models.material import Material, MaterialSupplier
from app.models.visiray import VisirayInventory, VisirayPartNumber, VisirayPartNumberVersion, VisirayVersionInventory
from app.services.material_code_service import MaterialCodeService
from app.utils.helpers import generate_code
from flask import current_app


class BOMService:
    """BOM management service."""

    BOM_STRUCTURE_REQUIRED_HEADERS = ['Bom编码', 'Bom名称']
    BOM_DETAIL_REQUIRED_HEADERS = ['Bom编码', '序号', '零件号', 'Bom用量']

    BOM_STRUCTURE_EXPORT_HEADERS = [
        'Bom编码',
        'Bom名称',
        '父Bom编码',
        '大类别',
        '版本号',
        '备注',
    ]

    BOM_DETAIL_EXPORT_HEADERS = [
        'Bom编码',
        '大类别',
        '中类别-1',
        '中类别-2',
        '小类别',
        '序号',
        '零件号',
        '版本号',
        '零件名称',
        'Bom用量',
        '备注',
        '单位',
    ]

    PART_CATEGORY_LABELS = {
        'processed': '加工件',
        'custom': '定制件',
        'standard': '标准件',
        'fastener': '紧固件',
        'chemical': '化学品',
        'tooling': '工装',
        'consumable': '辅助材料/耗材',
        'software': '软件',
        'product_bom': '产品BOM',
        'purchased': '外购件',
    }

    MAIN_CATEGORY_LABELS = {
        'processed_structure_machining': '结构件-机加工',
        'processed_structure_3d_printing': '结构件-3D打印',
        'processed_structure_sheet_metal': '结构件-折弯钣金',
        'processed_structure_molding': '结构件-成型',
        'processed_structure_standard_rework': '结构件-标准件再加工',
        'processed_optical_mirror': '光学件-反光镜',
        'processed_optical_lens': '光学件-透镜',
        'processed_optical_prism': '光学件-棱镜',
        'processed_optical_beamsplitter': '光学件-分光镜',
        'processed_optical_filter': '光学件-滤光片',
        'processed_electrical_pba': '电气件-PBA',
        'processed_electrical_wire': '电气件-线材',
        'processed_other': '其它',
        'custom_part': '零件',
        'custom_product': '产品',
        'standard_mechanical': '机械类',
        'standard_optical': '光学类',
        'standard_electrical': '电气类',
        'fastener_screw': '螺丝类',
        'fastener_nut': '螺母类',
        'fastener_washer': '垫片类',
        'fastener_spring': '弹簧类',
        'fastener_pin': '销钉类',
        'fastener_clip': '线卡类',
        'chemical_developer': '显影类',
        'chemical_etching': '蚀刻类',
        'chemical_adhesive': '胶水类',
        'chemical_cleaning': '清洗类',
        'chemical_photosensitive_ink': '感光油墨',
        'tooling_default': '工装',
        'consumable_default': '辅助材料/耗材',
        'software_default': '软件',
        'product_bom_default': '产品BOM',
        'mechanical': '机械件',
        'optical': '光学件',
        'electrical': '电气件',
        'software': '软件',
        'chemical': '化学品',
    }

    SUB_CATEGORY_LABELS = {
        'material_aluminum': '铝',
        'material_plastic': '塑料',
        'material_steel': '钢',
        'material_glass': '玻璃',
        'material_other': '其它',
        'surface_sandblast': '喷砂',
        'surface_anodized': '阳极氧化',
        'surface_spray': '喷涂',
        'surface_sandblast_anodized': '喷砂+阳极氧化',
        'light_source': '光源器件类',
        'light_transmission': '光传输器件类',
        'lens_prism': '光学透镜/棱镜类',
        'optical_filter': '光学滤光片类',
        'optical_sensor': '光学传感器类',
        'light_modulator': '光调制器件类',
        'display_imaging': '显示与成像类',
        'optical_other': '其他',
        'aluminum_profile': '铝型材类',
        'transmission': '传动类',
        'fasteners': '紧固件类',
        'spring': '弹簧类',
        'net_filter': '网及筛滤器类',
        'mechanical_other': '其他',
        'iron_steel': '铁、钢、合金钢',
        'copper_aluminum_titanium': '铜、铝、钛及其合金',
        'other_metal': '其他金属',
        'plastic': '塑料类',
        'rubber': '橡胶类',
        'glass_ceramic': '玻璃、陶瓷等',
        'passive': '被动元件类',
        'semiconductor': '半导体器件类',
        'electromechanical': '机电与连接类',
        'power': '电源与储能类',
        'sensor': '传感器类',
        'electrical_other': '其他',
        'custom_power': '电源与储能类',
        'custom_sensor': '传感器类',
        'wire_harness': '线束类',
        'drive_control': '驱控类',
        'system_software': '系统与基础软件',
        'office_software': '通用办公软件',
        'security_software': '安全与管理软件',
        'engineering_software': '工程与研发通用软件',
        'development_tools': '开发工具',
        'custom_platform': '定制平台类',
        'custom_development_tools': '定制研发工具',
        'custom_information_visualization': '定制信息化与可视化',
        'inorganic': '基础无机化学品',
        'organic': '有机化学品',
        'reagent': '试剂与实验室化学品',
        'functional': '功能化学品',
        'material_chemical': '材料化学品',
        'hazardous': '危险化学品',
        'custom_formulation': '定制配方化学品',
        'custom_polymer': '定制高分子材料',
        'custom_coating': '定制涂层与胶粘剂',
        'custom_functional': '定制功能化学品',
        'custom_material': '定制材料化学品',
        'custom_environmental': '定制环境与工业化学品',
    }

    @staticmethod
    def create_bom(data: Dict[str, Any], created_by: int) -> BOM:
        if not data.get('bom_code'):
            data['bom_code'] = BOMService._generate_bom_code(data.get('product_name', 'BOM'))

        if BOM.query.filter_by(bom_code=data['bom_code']).first():
            raise ValueError(f"BOM code {data['bom_code']} already exists")

        bom = BOM(
            bom_code=data['bom_code'],
            product_name=data['product_name'],
            product_model=data.get('product_model'),
            product_spec=data.get('product_spec'),
            version=BOMService._normalize_bom_version(data.get('version')),
            parent_bom_id=data.get('parent_bom_id'),
            status=BOMService._normalize_status(data.get('status', 'draft')),
            base_quantity=BOMService._to_float(data.get('base_quantity', 1.0), default=1.0),
            unit=data.get('unit', 'pcs'),
            process_route=data.get('process_route'),
            lead_time=data.get('lead_time'),
            effective_date=BOMService._parse_datetime(data.get('effective_date')),
            expiry_date=BOMService._parse_datetime(data.get('expiry_date')),
            remark=data.get('remark'),
            created_by=created_by,
        )

        db.session.add(bom)
        db.session.flush()

        if data.get('items') is not None:
            BOMService._replace_bom_items(bom.id, data.get('items') or [], created_by)

        BOMService._recalculate_bom_and_references(bom.id)
        db.session.commit()
        return bom

    @staticmethod
    def update_bom(bom_id: int, data: Dict[str, Any]) -> BOM:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        updatable_fields = [
            'product_name',
            'product_model',
            'product_spec',
            'version',
            'parent_bom_id',
            'base_quantity',
            'unit',
            'process_route',
            'lead_time',
            'effective_date',
            'expiry_date',
            'remark',
            'status',
        ]

        for field in updatable_fields:
            if field in data:
                if field in ['effective_date', 'expiry_date']:
                    setattr(bom, field, BOMService._parse_datetime(data.get(field)))
                elif field == 'base_quantity':
                    setattr(bom, field, BOMService._to_float(data[field], default=1.0))
                elif field == 'status':
                    setattr(bom, field, BOMService._normalize_status(data.get(field)))
                elif field == 'version':
                    setattr(bom, field, BOMService._normalize_bom_version(data.get(field)))
                else:
                    setattr(bom, field, data[field])

        if 'items' in data:
            BOMService._replace_bom_items(
                bom_id,
                data.get('items') or [],
                bom.created_by,
                allow_existing_inactive_sub_boms=True,
            )

        BOMService._recalculate_bom_and_references(bom.id)
        db.session.commit()
        return bom

    @staticmethod
    def delete_bom(bom_id: int, deleted_by: Optional[int] = None) -> bool:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            return False

        if BOM.query.filter_by(parent_bom_id=bom_id, is_deleted=False).first():
            raise ValueError("This BOM has child BOMs and cannot be deleted")

        referencing_items = BOMItem.query.filter_by(sub_bom_id=bom_id).all()
        referencing_bom_ids = {item.bom_id for item in referencing_items if item.bom_id}

        for item in referencing_items:
            BOMService._delete_bom_item_branch(item)

        version = bom.create_version("删除前快照")
        version.change_type = 'delete'
        version.change_reason = 'soft delete'
        if deleted_by is not None:
            version.created_by = deleted_by

        bom.is_deleted = True
        bom.deleted_at = datetime.utcnow()
        bom.deleted_by = deleted_by
        db.session.flush()
        for parent_bom_id in referencing_bom_ids:
            BOMService._recalculate_bom_and_references(parent_bom_id)
        db.session.commit()
        return True

    @staticmethod
    def get_bom_tree(bom_id: int) -> Dict[str, Any]:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        return {
            'bom': bom.to_dict(),
            'tree': bom.get_tree_structure(),
        }

    @staticmethod
    def create_version(bom_id: int, version_note: str, created_by: int) -> BOMVersion:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        version = bom.create_version(version_note)
        version.created_by = created_by
        db.session.commit()
        return version

    @staticmethod
    def upgrade_bom(bom_id: int, created_by: int) -> BOM:
        source = BOMService._get_active_bom(bom_id)
        if not source:
            raise ValueError("BOM does not exist")

        upgraded_bom = BOMService._copy_bom_for_upgrade(source, created_by, {}, source.id)
        BOMService._recalculate_bom_and_references(upgraded_bom.id)
        db.session.commit()
        return upgraded_bom

    @staticmethod
    def _copy_bom_for_upgrade(
        source: BOM,
        created_by: int,
        copied_boms: Dict[int, BOM],
        parent_bom_id: Optional[int],
    ) -> BOM:
        if source.id in copied_boms:
            return copied_boms[source.id]

        next_version = BOMService._next_bom_version(source.version)
        copied_bom = BOM(
            bom_code=BOMService._generate_upgraded_bom_code(source.bom_code, next_version),
            product_name=source.product_name,
            product_model=source.product_model,
            product_spec=source.product_spec,
            version=next_version,
            parent_bom_id=parent_bom_id,
            status=source.status,
            base_quantity=source.base_quantity,
            unit=source.unit,
            labor_cost=source.labor_cost,
            overhead_cost=source.overhead_cost,
            process_route=source.process_route,
            lead_time=source.lead_time,
            effective_date=source.effective_date,
            expiry_date=source.expiry_date,
            remark=source.remark,
            is_active=source.is_active,
            approved_by=source.approved_by,
            approved_at=source.approved_at,
            created_by=created_by,
        )
        db.session.add(copied_bom)
        db.session.flush()
        copied_boms[source.id] = copied_bom

        source_items = (
            source.bom_items
            .order_by(BOMItem.level, BOMItem.sort_order, BOMItem.id)
            .all()
        )
        item_id_map: Dict[int, BOMItem] = {}
        pending_parent_links: List[Tuple[BOMItem, Optional[int]]] = []
        for source_item in source_items:
            copied_sub_bom_id = source_item.sub_bom_id
            if source_item.sub_bom and not source_item.sub_bom.is_deleted:
                copied_sub_bom = BOMService._copy_bom_for_upgrade(
                    source_item.sub_bom,
                    created_by,
                    copied_boms,
                    source_item.sub_bom_id,
                )
                copied_sub_bom_id = copied_sub_bom.id

            copied_item = BOMItem(
                bom_id=copied_bom.id,
                material_id=source_item.material_id,
                sub_bom_id=copied_sub_bom_id,
                parent_item_id=None,
                level=source_item.level,
                sort_order=source_item.sort_order,
                item_no=source_item.item_no,
                quantity=source_item.quantity,
                unit=source_item.unit,
                is_key_material=source_item.is_key_material,
                is_optional=source_item.is_optional,
                usage_rate=source_item.usage_rate,
                selected_supplier_id=source_item.selected_supplier_id,
                selected_supplier_price=BOMService._item_price_snapshot(source_item),
                substitute_group=source_item.substitute_group,
                substitute_priority=source_item.substitute_priority,
                process_step=source_item.process_step,
                assembly_note=source_item.assembly_note,
                effective_date=source_item.effective_date,
                expiry_date=source_item.expiry_date,
                remark=source_item.remark,
                is_active=source_item.is_active,
            )
            db.session.add(copied_item)
            db.session.flush()
            item_id_map[source_item.id] = copied_item
            pending_parent_links.append((copied_item, source_item.parent_item_id))

        for copied_item, source_parent_id in pending_parent_links:
            if source_parent_id:
                parent_item = item_id_map.get(source_parent_id)
                if not parent_item:
                    raise ValueError("BOM明细父子关系复制失败")
                copied_item.parent_item_id = parent_item.id

        db.session.flush()
        copied_bom.calculate_cost()
        db.session.flush()
        return copied_bom

    @staticmethod
    def _item_price_snapshot(item: BOMItem):
        if item.selected_supplier_price is not None:
            return item.selected_supplier_price
        if item.selected_supplier and item.selected_supplier.status == 'active':
            return item.selected_supplier.price
        if item.material:
            return item.get_unit_price()
        return None

    @staticmethod
    def recalculate_boms_for_material(
        material_id: int,
        selected_supplier_id: Optional[int] = None,
    ) -> None:
        items = BOMItem.query.filter_by(material_id=material_id).all()
        bom_ids = set()

        for item in items:
            selected_supplier = item.selected_supplier
            selected_supplier_matches_material = (
                selected_supplier is not None
                and int(selected_supplier.material_id) == int(material_id)
            )
            if (
                selected_supplier_id
                and item.selected_supplier_id == selected_supplier_id
                and selected_supplier_matches_material
            ):
                item.selected_supplier_price = (
                    selected_supplier.price
                    if selected_supplier and selected_supplier.status == 'active'
                    else None
                )
            elif (
                not selected_supplier
                or selected_supplier.status != 'active'
                or not selected_supplier_matches_material
            ):
                selected_supplier = BOMService._resolve_selected_supplier(
                    material_id,
                    None,
                    item.part_version_id,
                )
                item.selected_supplier_id = getattr(selected_supplier, 'id', None)
                item.selected_supplier_price = getattr(selected_supplier, 'price', None)

            if item.bom_id:
                bom_ids.add(item.bom_id)

        for bom_id in bom_ids:
            BOMService._recalculate_bom_and_references(bom_id)

    @staticmethod
    def update_item_supplier(bom_id: int, item_id: int, supplier_price_id: int) -> BOMItem:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        item = BOMItem.query.filter_by(id=item_id, bom_id=bom_id).first()
        if not item:
            raise ValueError("BOM明细不存在")
        if not item.material_id:
            raise ValueError("只有零件明细可以切换供应商")

        supplier_price = MaterialSupplier.query.get(supplier_price_id)
        if not supplier_price or supplier_price.status != 'active':
            raise ValueError("供应商报价不存在或已停用")
        if int(supplier_price.material_id) != int(item.material_id):
            raise ValueError("供应商报价不属于当前零件")
        if item.part_version_id is not None and supplier_price.part_version_id not in (None, item.part_version_id):
            raise ValueError("供应商报价版本不匹配")

        item.selected_supplier_id = supplier_price.id
        item.selected_supplier_price = supplier_price.price
        BOMService._recalculate_bom_and_references(bom.id)
        db.session.commit()
        return item

    @staticmethod
    def update_item_part_version(bom_id: int, item_id: int, part_version_id: Optional[int]) -> BOMItem:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        item = BOMItem.query.filter_by(id=item_id, bom_id=bom_id).first()
        if not item:
            raise ValueError("BOM明细不存在")
        if not item.material_id or not item.material:
            raise ValueError("只有零件明细可以切换版本")

        part_id = item._display_material_code()
        part = VisirayPartNumber.query.get(part_id) if part_id else None
        if not part:
            raise ValueError("该明细未关联有效零件号")

        resolved_version_id = BOMService._resolve_bom_part_version(part, part_version_id)
        selected_supplier = BOMService._resolve_selected_supplier(item.material_id, None, resolved_version_id)

        item.part_version_id = resolved_version_id
        item.selected_supplier_id = getattr(selected_supplier, 'id', None)
        item.selected_supplier_price = getattr(selected_supplier, 'price', None)
        BOMService._recalculate_bom_and_references(bom.id)
        db.session.commit()
        return item

    @staticmethod
    def get_bom_cost_analysis(bom_id: int) -> Dict[str, Any]:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        bom.calculate_cost()
        all_items = bom.bom_items.order_by(BOMItem.level, BOMItem.sort_order, BOMItem.id).all()
        root_items = [item for item in all_items if item.parent_item_id is None] or all_items
        cost_breakdown = []
        total_material_cost = sum(item.get_item_cost() for item in root_items)

        for item in all_items:
            item_cost = item.get_item_cost()
            cost_breakdown.append({
                'item_id': item.id,
                'material_code': item._display_material_code() if hasattr(item, '_display_material_code') else (item.material.material_code if item.material else None),
                'material_name': item.material.material_name if item.material else None,
                'quantity': float(item.quantity),
                'unit_price': float(item.get_unit_price()) if item.material else 0,
                'supplier_name': item.selected_supplier.supplier.supplier_name if item.selected_supplier and item.selected_supplier.supplier else None,
                'total_cost': float(item_cost),
                'usage_rate': float(item.usage_rate),
            })

        return {
            'bom_code': bom.bom_code,
            'product_name': bom.product_name,
            'total_cost': float(bom.total_cost or 0),
            'material_cost': float(total_material_cost),
            'labor_cost': float(bom.labor_cost or 0),
            'overhead_cost': float(bom.overhead_cost or 0),
            'cost_breakdown': cost_breakdown,
            'updated_at': bom.updated_at.isoformat() if bom.updated_at else None,
        }

    @staticmethod
    def get_bom_shortage(bom_id: int, production_quantity: Optional[float] = None) -> Dict[str, Any]:
        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        default_quantity = BOMService._to_float(bom.base_quantity, default=1.0)
        requested_quantity = BOMService._to_float(production_quantity, default=default_quantity)
        if requested_quantity <= 0:
            raise ValueError("查询数量必须大于0")

        requirements = BOMService._collect_bom_requirements(
            bom=bom,
            production_quantity=requested_quantity,
            visited=set(),
        )
        items = []
        for item in requirements.values():
            inventory_key = BOMService._inventory_key(item.get('part_id'))
            version_key = item.get('part_version_id')
            inventory = None
            if inventory_key is not None:
                if version_key is not None:
                    inventory = VisirayVersionInventory.query.filter_by(
                        goods_id=inventory_key,
                        part_version_id=version_key,
                    ).first()
                else:
                    inventory = VisirayInventory.query.get(inventory_key)
            stock_quantity = (
                BOMService._to_float(inventory.stock_quantity)
                if inventory is not None
                else BOMService._to_float(item.get('material_current_stock'))
            )
            required_quantity = BOMService._to_float(item.get('required_quantity'))
            shortage_quantity = max(required_quantity - stock_quantity, 0.0)
            items.append({
                'material_id': item.get('material_id'),
                'material_code': item.get('material_code'),
                'part_id': item.get('part_id'),
                'part_version_id': item.get('part_version_id'),
                'version_no': item.get('version_no'),
                'material_name': item.get('material_name'),
                'unit': item.get('unit') or (inventory.unit if inventory else None) or 'pcs',
                'required_quantity': required_quantity,
                'stock_quantity': stock_quantity,
                'shortage_quantity': shortage_quantity,
                'stock_source': 'visiray_inventory' if inventory is not None else 'material_current_stock',
                'inventory_goods_id': inventory.goods_id if inventory is not None else None,
                'inventory_name': inventory.goods_name if inventory is not None else None,
                'inventory_supplier': inventory.supplier if inventory is not None else None,
                'is_key_material': item.get('is_key_material', False),
                'is_optional': item.get('is_optional', False),
                'substitute_group': item.get('substitute_group'),
                'substitute_priority': item.get('substitute_priority'),
                'paths': item.get('paths') or [],
            })

        items.sort(key=lambda row: (row['shortage_quantity'] <= 0, row.get('part_id') or row.get('material_code') or '', row.get('version_no') or ''))
        shortage_items = [item for item in items if item['shortage_quantity'] > 0]

        return {
            'bom_id': bom.id,
            'bom_code': bom.bom_code,
            'product_name': bom.product_name,
            'base_quantity': BOMService._to_float(bom.base_quantity, default=1.0),
            'production_quantity': requested_quantity,
            'items': items,
            'shortage_items': shortage_items,
            'summary': {
                'item_count': len(items),
                'shortage_item_count': len(shortage_items),
                'total_required_quantity': sum(item['required_quantity'] for item in items),
                'total_stock_quantity': sum(item['stock_quantity'] for item in items),
                'total_shortage_quantity': sum(item['shortage_quantity'] for item in shortage_items),
            },
        }

    @staticmethod
    def import_boms_from_excel(upload_file, created_by: int) -> Dict[str, Any]:
        from openpyxl import load_workbook

        workbook = load_workbook(upload_file, read_only=True, data_only=True)
        errors: List[Dict[str, Any]] = []
        structure_rows: List[Dict[str, Any]] = []
        detail_rows: List[Dict[str, Any]] = []

        def add_error(sheet: str, row: int, message: str) -> None:
            if len(errors) < 100:
                errors.append({'sheet': sheet, 'row': row, 'message': message})

        for sheet_index, sheet in enumerate(workbook.worksheets):
            preferred_type = 'structure' if sheet_index == 0 else 'detail' if sheet_index == 1 else None
            header_info = BOMService._find_two_sheet_bom_header(sheet, preferred_type)
            if not header_info:
                continue

            table_type, header_map, header_row_number = header_info
            for row_number, row in enumerate(sheet.iter_rows(min_row=header_row_number + 1, values_only=True), header_row_number + 1):
                if table_type == 'structure':
                    row_data = BOMService._parse_bom_structure_row(sheet.title, row_number, row, header_map)
                    if row_data is not None:
                        structure_rows.append(row_data)
                else:
                    row_data = BOMService._parse_bom_detail_row(sheet.title, row_number, row, header_map)
                    if row_data is not None:
                        detail_rows.append(row_data)

        if not structure_rows:
            raise ValueError("没有找到BOM结构表，请确认第一个Sheet包含：Bom编码、Bom名称、父Bom编码")
        if not detail_rows:
            raise ValueError("没有找到BOM明细表，请确认第二个Sheet包含：Bom编码、序号、零件号、Bom用量")

        bom_defs: Dict[str, Dict[str, Any]] = {}
        for row in structure_rows:
            bom_code = row['bom_code']
            if bom_code in bom_defs:
                add_error(row['sheet'], row['row'], f"BOM编码 {bom_code} 在结构表中重复")
                continue
            bom_defs[bom_code] = {
                'bom_code': bom_code,
                'product_name': row['product_name'],
                'version': row.get('version') or '0001',
                'parent_code': row.get('parent_code'),
                'remark': row.get('remark'),
                'items': [],
            }

        used_item_numbers: Dict[str, Set[str]] = {}
        for row in structure_rows:
            child_code = row['bom_code']
            parent_code = row.get('parent_code')
            if not parent_code:
                continue
            parent_def = bom_defs.get(parent_code)
            if not parent_def:
                continue

            item_no = row.get('item_no') or str(len(parent_def['items']) + 1)
            item_key = str(item_no)
            if item_key in used_item_numbers.setdefault(parent_code, set()):
                add_error(row['sheet'], row['row'], f"BOM {parent_code} 下序号 {item_key} 重复")
            used_item_numbers[parent_code].add(item_key)
            parent_def['items'].append({
                'sheet': row['sheet'],
                'row': row['row'],
                'bom_code': parent_code,
                'item_no': item_no,
                'item_type': 'sub_bom',
                'item_code': child_code,
                'item_name': row['product_name'],
                'quantity': BOMService._to_float(row.get('quantity'), default=1.0) or 1.0,
                'unit': 'pcs',
                'usage_rate': 1.0,
                'is_optional': False,
                'remark': row.get('remark'),
            })

        for row in detail_rows:
            bom_code = row['bom_code']
            current = bom_defs.get(bom_code)
            if not current:
                add_error(row['sheet'], row['row'], f"明细所属BOM {bom_code} 不在BOM结构表中")
                continue

            item_key = str(row['item_no'])
            if item_key in used_item_numbers.setdefault(bom_code, set()):
                add_error(row['sheet'], row['row'], f"BOM {bom_code} 下序号 {item_key} 重复")
            used_item_numbers[bom_code].add(item_key)

            if row.get('item_code') in bom_defs:
                row['item_type'] = 'sub_bom'
            else:
                row['item_type'] = 'part'
            current['items'].append(row)

        # BOM明细中的类别是当前业务分类，不能再根据老零件号反推。
        # 同一份文件内同一个零件号如果出现不同类别，必须先人工确认，避免随机覆盖主数据。
        imported_part_categories: Dict[str, Tuple[str, str, str]] = {}
        imported_part_category_rows: Dict[str, Tuple[str, int]] = {}
        for bom_def in bom_defs.values():
            for row in bom_def.get('items') or []:
                if row.get('item_type') != 'part':
                    continue
                category_values = (
                    row.get('category') or '',
                    row.get('main_type') or '',
                    row.get('sub_type') or '',
                )
                if not any(category_values):
                    continue

                part_id = row['item_code']
                previous = imported_part_categories.get(part_id)
                if previous and previous != category_values:
                    previous_sheet, previous_row = imported_part_category_rows[part_id]
                    add_error(
                        row['sheet'],
                        row['row'],
                        f"零件号 {part_id} 在导入文件中类别不一致："
                        f"{previous}（{previous_sheet} 第{previous_row}行）与 {category_values}",
                    )
                    continue
                imported_part_categories[part_id] = category_values
                imported_part_category_rows.setdefault(part_id, (row['sheet'], row['row']))

        for bom_code, bom_def in bom_defs.items():
            parent_code = bom_def.get('parent_code')
            if parent_code and parent_code not in bom_defs and not BOM.query.filter_by(bom_code=parent_code, is_deleted=False).first():
                first_row = bom_def['items'][0]
                add_error(first_row['sheet'], first_row['row'], f"父BOM编码 {parent_code} 不存在，也没有在当前Excel中定义")

            for row in bom_def.get('items') or []:
                if row['item_type'] == 'part':
                    part = VisirayPartNumber.query.get(row['item_code'])
                    if not part:
                        add_error(row['sheet'], row['row'], f"零件号 {row['item_code']} 不存在")
                    elif row.get('part_version_no') and not BOMService._find_part_version_by_no(part.part_id, row['part_version_no']):
                        add_error(row['sheet'], row['row'], f"零件号 {row['item_code']} 下不存在版本 {row['part_version_no']}")
                elif row['item_type'] == 'sub_bom':
                    if row['item_code'] == bom_code:
                        add_error(row['sheet'], row['row'], "BOM不能引用自己作为子BOM")
                    elif row['item_code'] not in bom_defs and not BOM.query.filter_by(bom_code=row['item_code'], is_deleted=False).first():
                        add_error(row['sheet'], row['row'], f"子BOM编码 {row['item_code']} 不存在，也没有在当前Excel中定义")
                else:
                    add_error(row['sheet'], row['row'], "项目类型必须是零件或子BOM")

        BOMService._validate_imported_bom_graph(bom_defs, errors)
        if errors:
            raise ValueError(BOMService._format_import_errors(errors))

        created_count = 0
        updated_count = 0
        bom_by_code: Dict[str, BOM] = {}

        for bom_code, bom_def in bom_defs.items():
            bom = BOM.query.filter_by(bom_code=bom_code).first()
            if bom:
                if not bom.is_deleted:
                    bom.create_version("Excel导入前快照")
                bom.product_name = bom_def['product_name']
                bom.version = bom_def['version']
                bom.remark = bom_def.get('remark')
                bom.status = BOMService._normalize_status(getattr(bom, 'status', None) or 'draft')
                bom.is_deleted = False
                bom.deleted_at = None
                bom.deleted_by = None
                bom.is_active = True
                bom.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                bom = BOM(
                    bom_code=bom_code,
                    product_name=bom_def['product_name'],
                    version=bom_def['version'],
                    status='draft',
                    base_quantity=1.0,
                    unit='pcs',
                    remark=bom_def.get('remark'),
                    created_by=created_by,
                )
                db.session.add(bom)
                created_count += 1
            bom_by_code[bom_code] = bom

        db.session.flush()

        for bom_code, bom_def in bom_defs.items():
            parent_code = bom_def.get('parent_code')
            bom = bom_by_code[bom_code]
            bom.parent_bom_id = None
            if parent_code:
                parent_bom = bom_by_code.get(parent_code) or BOM.query.filter_by(bom_code=parent_code, is_deleted=False).first()
                if not parent_bom:
                    raise ValueError(f"BOM {bom_code} 的父BOM {parent_code} 不存在")
                if int(parent_bom.id) == int(bom.id):
                    raise ValueError(f"BOM {bom_code} 不能把自己设为父BOM")
                bom.parent_bom_id = parent_bom.id

        db.session.flush()

        for part_id, category_values in imported_part_categories.items():
            part = VisirayPartNumber.query.get(part_id)
            if not part:
                # 零件号存在性已经在上面的校验阶段处理，这里只防御性保护。
                continue
            part.category, part.main_type, part.sub_type = category_values

        for bom_code, bom_def in bom_defs.items():
            bom = bom_by_code[bom_code]
            BOMService._replace_bom_items_from_import(bom, bom_def['items'], bom_by_code, created_by)

        for bom in bom_by_code.values():
            BOMService._recalculate_bom_and_references(bom.id)

        db.session.commit()
        return {
            'created_count': created_count,
            'updated_count': updated_count,
            'item_count': len(detail_rows),
            'bom_codes': list(bom_by_code.keys()),
        }

    @staticmethod
    def export_bom_to_excel(bom_id: int) -> Tuple[str, BytesIO]:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter

        bom = BOMService._get_active_bom(bom_id)
        if not bom:
            raise ValueError("BOM does not exist")

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'BOM导出'
        sheet.append(BOMService.BOM_STRUCTURE_EXPORT_HEADERS)

        for cell in sheet[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='4F81BD')

        export_boms, parent_info_by_bom_id = BOMService._collect_boms_for_export(bom)
        for current_bom in export_boms:
            parent_info = parent_info_by_bom_id.get(current_bom.id, {})
            parent_code = parent_info.get('parent_code', '')
            is_root_bom = current_bom.id == bom.id

            sheet.append([
                current_bom.bom_code,
                current_bom.product_name,
                parent_code,
                '产品Bom' if is_root_bom else '子Bom',
                format_bom_version(current_bom.version),
                current_bom.remark or '',
            ])

        detail_header_row = sheet.max_row + 2
        sheet.append([])
        sheet.append(BOMService.BOM_DETAIL_EXPORT_HEADERS)
        for cell in sheet[detail_header_row]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='70AD47')

        for current_bom in export_boms:
            items = current_bom.bom_items.order_by(BOMItem.sort_order, BOMItem.id).all()
            export_item_no = 0
            for item in items:
                if not item.material_id:
                    continue
                # 导出序号表示当前BOM明细的显示顺序，不沿用历史item_no，避免删除或调整明细后出现断号。
                export_item_no += 1
                item_code = item._display_material_code()
                item_name = item.material.material_name if item.material else ''
                category_values = BOMService._part_category_values(item)
                main_category, sub_category_group = BOMService._split_export_main_category(category_values[1])
                quantity = BOMService._to_float(item.quantity)
                sheet.append([
                    current_bom.bom_code,
                    category_values[0],
                    main_category,
                    sub_category_group,
                    category_values[2],
                    export_item_no,
                    item_code,
                    BOMService._part_version_no(item.part_version_id),
                    item_name,
                    quantity,
                    item.remark or '',
                    item.unit or (item.material.unit if item.material else '') or '',
                ])

        sheet.freeze_panes = 'A2'
        max_columns = max(len(BOMService.BOM_STRUCTURE_EXPORT_HEADERS), len(BOMService.BOM_DETAIL_EXPORT_HEADERS))
        for column_index in range(1, max_columns + 1):
            width = 12
            for row in sheet.iter_rows(min_row=2, min_col=column_index, max_col=column_index, values_only=True):
                value = row[0]
                if value is not None:
                    width = max(width, min(len(str(value)) + 4, 36))
            sheet.column_dimensions[get_column_letter(column_index)].width = width

        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        filename = f"{bom.bom_code}_BOM.xlsx"
        return filename, stream

    @staticmethod
    def search_boms(filters: Dict[str, Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        query = BOM.query.filter(BOM.is_deleted.is_(False))

        if filters.get('keyword'):
            keyword = f"%{filters['keyword']}%"
            query = query.filter(
                or_(
                    BOM.bom_code.like(keyword),
                    BOM.product_name.like(keyword),
                    BOM.product_model.like(keyword),
                )
            )

        if filters.get('status'):
            query = query.filter(BOM.status == filters['status'])

        if filters.get('created_by'):
            query = query.filter(BOM.created_by == filters['created_by'])

        if filters.get('date_from'):
            query = query.filter(BOM.created_at >= datetime.fromisoformat(filters['date_from']))

        if filters.get('date_to'):
            query = query.filter(BOM.created_at <= datetime.fromisoformat(filters['date_to']))

        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')

        if hasattr(BOM, sort_by):
            order_field = getattr(BOM, sort_by)
            if sort_order == 'desc':
                order_field = order_field.desc()
            query = query.order_by(order_field)

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [bom.to_dict() for bom in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page,
            'per_page': paginated.per_page,
            'has_prev': paginated.has_prev,
            'has_next': paginated.has_next,
        }

    @staticmethod
    def _find_two_sheet_bom_header(sheet, preferred_type: Optional[str] = None) -> Optional[Tuple[str, Dict[str, int], int]]:
        for row_number, row in enumerate(sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 1, 20), values_only=True), 1):
            header_map = BOMService._build_two_sheet_header_map(row)
            if preferred_type == 'structure' and {'bom_code', 'product_name'}.issubset(header_map.keys()):
                return 'structure', header_map, row_number
            if preferred_type == 'detail' and {'bom_code', 'item_no', 'item_code', 'quantity'}.issubset(header_map.keys()):
                return 'detail', header_map, row_number
            if {'bom_code', 'product_name'}.issubset(header_map.keys()) and 'item_code' not in header_map:
                return 'structure', header_map, row_number
            if {'bom_code', 'item_no', 'item_code', 'quantity'}.issubset(header_map.keys()):
                return 'detail', header_map, row_number
        return None

    @staticmethod
    def _build_two_sheet_header_map(row) -> Dict[str, int]:
        aliases = {
            'bom编码': 'bom_code',
            'bomcode': 'bom_code',
            'bom名称': 'product_name',
            'bomname': 'product_name',
            '父bom编码': 'parent_code',
            '父bom': 'parent_code',
            '大类别': 'category',
            '中类别': 'main_category',
            '中类别1': 'main_category',
            '中类别-1': 'main_category',
            '中类别2': 'sub_category_group',
            '中类别-2': 'sub_category_group',
            '小类别': 'sub_category',
            '序号': 'item_no',
            '零件号': 'item_code',
            '零件号/bom编号': 'item_code',
            '零件号/bom编码': 'item_code',
            '项目编码': 'item_code',
            '版本号': 'version',
            '零件名称': 'item_name',
            '项目名称': 'item_name',
            'bom用量': 'quantity',
            '用量': 'quantity',
            '数量': 'quantity',
            '备注': 'remark',
            '供应商': 'supplier',
            '单价': 'price',
            '合计': 'total_price',
            '库存': 'stock',
            '缺料': 'shortage',
            '单位': 'unit',
            '损耗率': 'usage_rate',
            '是否可选': 'is_optional',
        }
        header_map: Dict[str, int] = {}
        seen_names: Dict[str, int] = {}
        for index, value in enumerate(row or []):
            raw_key = BOMService._normalize_header(value)
            if raw_key == '中类别':
                seen_count = seen_names.get(raw_key, 0)
                seen_names[raw_key] = seen_count + 1
                mapped = 'main_category' if seen_count == 0 else 'sub_category_group'
            else:
                mapped = aliases.get(raw_key)
            if mapped and mapped not in header_map:
                header_map[mapped] = index
        return header_map

    @staticmethod
    def _parse_bom_structure_row(sheet: str, row_number: int, row, header_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        def value(field: str):
            index = header_map.get(field)
            return row[index] if index is not None and index < len(row) else None

        raw_values = [BOMService._clean_excel_cell(item) for item in row or []]
        if not any(raw_values):
            return None

        bom_code = BOMService._clean_excel_cell(value('bom_code'))
        product_name = BOMService._clean_excel_cell(value('product_name'))
        if not bom_code and not product_name:
            return None

        missing = []
        if not bom_code:
            missing.append('Bom编码')
        if not product_name:
            missing.append('Bom名称')
        if missing:
            raise ValueError(f"{sheet} 第{row_number}行缺少必填字段：{', '.join(missing)}")

        quantity = BOMService._to_float(value('quantity'), default=1.0)
        if quantity <= 0:
            raise ValueError(f"{sheet} 第{row_number}行Bom用量必须大于0")

        return {
            'sheet': sheet,
            'row': row_number,
            'bom_code': bom_code,
            'product_name': product_name,
            'parent_code': BOMService._clean_excel_cell(value('parent_code')),
            'item_no': BOMService._clean_excel_cell(value('item_no')),
            'version': BOMService._normalize_bom_version(value('version')),
            'quantity': quantity,
            'remark': BOMService._clean_excel_cell(value('remark')),
        }

    @staticmethod
    def _parse_bom_detail_row(sheet: str, row_number: int, row, header_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        def value(field: str):
            index = header_map.get(field)
            return row[index] if index is not None and index < len(row) else None

        raw_values = [BOMService._clean_excel_cell(item) for item in row or []]
        if not any(raw_values):
            return None

        bom_code = BOMService._clean_excel_cell(value('bom_code'))
        item_no = BOMService._clean_excel_cell(value('item_no'))
        item_code = BOMService._clean_excel_cell(value('item_code'))
        item_name = BOMService._clean_excel_cell(value('item_name'))
        part_version_no = BOMService._clean_excel_version(value('version'), four_digit=True)
        category, main_type, sub_type = BOMService._normalize_imported_part_categories(
            value('category'),
            value('main_category'),
            value('sub_category_group'),
            value('sub_category'),
        )
        if not any([bom_code, item_no, item_code, item_name, BOMService._clean_excel_cell(value('quantity'))]):
            return None

        missing = []
        if not bom_code:
            missing.append('Bom编码')
        if not item_no:
            missing.append('序号')
        if not item_code:
            missing.append('零件号')
        if missing:
            raise ValueError(f"{sheet} 第{row_number}行缺少必填字段：{', '.join(missing)}")

        quantity = BOMService._to_float(value('quantity'), default=0.0)
        if quantity <= 0:
            raise ValueError(f"{sheet} 第{row_number}行Bom用量必须大于0")

        usage_rate = BOMService._to_float(value('usage_rate'), default=1.0)
        if usage_rate <= 0:
            raise ValueError(f"{sheet} 第{row_number}行损耗率必须大于0")

        return {
            'sheet': sheet,
            'row': row_number,
            'bom_code': bom_code,
            'item_no': item_no,
            'item_type': 'part',
            'item_code': item_code,
            'part_version_no': part_version_no,
            'category': category,
            'main_type': main_type,
            'sub_type': sub_type,
            'item_name': item_name,
            'quantity': quantity,
            'unit': BOMService._clean_excel_cell(value('unit')) or 'pcs',
            'usage_rate': usage_rate,
            'is_optional': BOMService._parse_yes_no(value('is_optional')),
            'remark': BOMService._clean_excel_cell(value('remark')),
        }

    @staticmethod
    def _find_bom_import_header(row) -> Optional[Dict[str, int]]:
        aliases = {
            'bom编码': 'bom_code',
            'bomcode': 'bom_code',
            'bom名称': 'product_name',
            'bomname': 'product_name',
            '产品名称': 'product_name',
            '版本号': 'version',
            '版本': 'version',
            '父bom编码': 'parent_code',
            '父bom': 'parent_code',
            '序号': 'item_no',
            '项目号': 'item_no',
            '项目类型': 'item_type',
            '类型': 'item_type',
            '项目编码': 'item_code',
            '零件号/bom编码': 'item_code',
            '项目名称': 'item_name',
            'bom用量': 'quantity',
            '用量': 'quantity',
            '数量': 'quantity',
            '单位': 'unit',
            '损耗率': 'usage_rate',
            '是否可选': 'is_optional',
            '可选': 'is_optional',
            '备注': 'remark',
        }
        header_map: Dict[str, int] = {}
        for index, value in enumerate(row or []):
            key = BOMService._normalize_header(value)
            mapped = aliases.get(key)
            if mapped and mapped not in header_map:
                header_map[mapped] = index

        required = {'bom_code', 'product_name', 'version', 'item_no', 'item_type', 'item_code', 'quantity'}
        return header_map if required.issubset(header_map.keys()) else None

    @staticmethod
    def _parse_bom_import_row(sheet: str, row_number: int, row, header_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        def value(field: str):
            index = header_map.get(field)
            return row[index] if index is not None and index < len(row) else None

        raw_values = [BOMService._clean_excel_cell(item) for item in row or []]
        if not any(raw_values):
            return None

        bom_code = BOMService._clean_excel_cell(value('bom_code'))
        product_name = BOMService._clean_excel_cell(value('product_name'))
        version = BOMService._normalize_bom_version(value('version'))
        item_no = BOMService._clean_excel_cell(value('item_no'))
        item_type = BOMService._normalize_import_item_type(value('item_type'))
        item_code = BOMService._clean_excel_cell(value('item_code'))

        missing = []
        if not bom_code:
            missing.append('BOM编码')
        if not product_name:
            missing.append('BOM名称')
        if not item_no:
            missing.append('序号')
        if not item_type:
            missing.append('项目类型')
        if not item_code:
            missing.append('项目编码')
        if missing:
            raise ValueError(f"{sheet} 第{row_number}行缺少必填字段：{', '.join(missing)}")

        quantity = BOMService._to_float(value('quantity'), default=0.0)
        if quantity <= 0:
            raise ValueError(f"{sheet} 第{row_number}行BOM用量必须大于0")

        usage_rate = BOMService._to_float(value('usage_rate'), default=1.0)
        if usage_rate <= 0:
            raise ValueError(f"{sheet} 第{row_number}行损耗率必须大于0")

        return {
            'sheet': sheet,
            'row': row_number,
            'bom_code': bom_code,
            'product_name': product_name,
            'version': version,
            'parent_code': BOMService._clean_excel_cell(value('parent_code')),
            'item_no': item_no,
            'item_type': item_type,
            'item_code': item_code,
            'item_name': BOMService._clean_excel_cell(value('item_name')),
            'quantity': quantity,
            'unit': BOMService._clean_excel_cell(value('unit')) or 'pcs',
            'usage_rate': usage_rate,
            'is_optional': BOMService._parse_yes_no(value('is_optional')),
            'remark': BOMService._clean_excel_cell(value('remark')),
        }

    @staticmethod
    def _replace_bom_items_from_import(
        bom: BOM,
        rows: List[Dict[str, Any]],
        imported_boms: Dict[str, BOM],
        created_by: Optional[int],
    ) -> None:
        existing_items = (
            BOMItem.query.filter_by(bom_id=bom.id)
            .order_by(BOMItem.level.desc(), BOMItem.id.desc())
            .all()
        )
        for item in existing_items:
            db.session.delete(item)
        db.session.flush()

        sorted_rows = sorted(rows, key=lambda item: BOMService._sort_key(item.get('item_no')))
        for index, row in enumerate(sorted_rows, 1):
            material_id = None
            part_version_id = None
            sub_bom_id = None
            if row['item_type'] == 'part':
                part = VisirayPartNumber.query.get(row['item_code'])
                if not part:
                    raise ValueError(f"零件号 {row['item_code']} 不存在")
                if row.get('part_version_no'):
                    version = BOMService._find_part_version_by_no(part.part_id, row['part_version_no'])
                    if not version:
                        raise ValueError(f"零件号 {row['item_code']} 下不存在版本 {row['part_version_no']}")
                    if version.status != 'active':
                        raise ValueError(f"零件号 {row['item_code']} 的版本 {row['part_version_no']} 已废弃，不能加入新BOM")
                    part_version_id = version.id
                # Excel未填写版本号时保留NULL，不自动绑定当前版本。
                material_id = BOMService._get_or_create_material_from_part(row['item_code'], created_by)
            else:
                sub_bom = imported_boms.get(row['item_code']) or BOM.query.filter_by(bom_code=row['item_code'], is_deleted=False).first()
                if not sub_bom:
                    raise ValueError(f"子BOM {row['item_code']} 不存在")
                if int(sub_bom.id) == int(bom.id):
                    raise ValueError("BOM不能引用自己作为子BOM")
                sub_bom_id = sub_bom.id

            selected_supplier = BOMService._resolve_selected_supplier(material_id, None, part_version_id)
            db.session.add(BOMItem(
                bom_id=bom.id,
                material_id=material_id,
                part_version_id=part_version_id,
                sub_bom_id=sub_bom_id,
                level=1,
                sort_order=index,
                item_no=row['item_no'],
                quantity=row['quantity'],
                unit=row.get('unit'),
                is_optional=row.get('is_optional', False),
                usage_rate=row.get('usage_rate', 1.0),
                selected_supplier_id=getattr(selected_supplier, 'id', None),
                selected_supplier_price=getattr(selected_supplier, 'price', None),
                remark=row.get('remark'),
            ))

        db.session.flush()

    @staticmethod
    def _delete_bom_item_branch(item: BOMItem) -> None:
        children = sorted(
            list(item.child_items or []),
            key=lambda child: ((child.level or 0), child.id or 0),
            reverse=True,
        )
        for child in children:
            BOMService._delete_bom_item_branch(child)
        db.session.delete(item)

    @staticmethod
    def _validate_imported_bom_graph(bom_defs: Dict[str, Dict[str, Any]], errors: List[Dict[str, Any]]) -> None:
        graph: Dict[str, List[str]] = {code: [] for code in bom_defs.keys()}
        for bom_code, bom_def in bom_defs.items():
            parent_code = bom_def.get('parent_code')
            if parent_code:
                if parent_code == bom_code:
                    errors.append({'sheet': '', 'row': '', 'message': f"BOM {bom_code} 不能把自己设为父BOM"})
                elif parent_code in bom_defs:
                    graph.setdefault(parent_code, []).append(bom_code)
            for item in bom_def.get('items') or []:
                if item.get('item_type') == 'sub_bom' and item.get('item_code') in bom_defs:
                    graph.setdefault(bom_code, []).append(item['item_code'])

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(code: str, path: List[str]) -> None:
            if code in visiting:
                errors.append({'sheet': '', 'row': '', 'message': f"BOM存在循环引用：{' -> '.join(path + [code])}"})
                return
            if code in visited:
                return
            visiting.add(code)
            for child_code in graph.get(code, []):
                dfs(child_code, path + [code])
            visiting.remove(code)
            visited.add(code)

        for code in graph.keys():
            dfs(code, [])

    @staticmethod
    def _collect_boms_for_export(root_bom: BOM) -> Tuple[List[BOM], Dict[int, Dict[str, Any]]]:
        result: List[BOM] = []
        parent_info_by_bom_id: Dict[int, Dict[str, Any]] = {}
        visited: Set[int] = set()

        def walk(bom: BOM, parent_code: str = '', parent_item: Optional[BOMItem] = None) -> None:
            if not bom or bom.is_deleted or bom.id in visited:
                return
            visited.add(bom.id)
            parent_info_by_bom_id[bom.id] = {
                'parent_code': parent_code,
                'item': parent_item,
            }
            result.append(bom)
            items = bom.bom_items.order_by(BOMItem.sort_order, BOMItem.id).all()
            for item in items:
                if item.sub_bom and not item.sub_bom.is_deleted:
                    walk(item.sub_bom, bom.bom_code, item)

        walk(root_bom)
        return result, parent_info_by_bom_id

    @staticmethod
    def _part_category_values(item: BOMItem) -> Tuple[str, str, str]:
        if not item.material:
            return '', '', ''
        part_id = BOMService._material_part_id(item.material)
        if not part_id:
            return '', '', ''
        part = VisirayPartNumber.query.get(part_id)
        if not part:
            return '', '', ''
        return (
            BOMService._label_or_raw(BOMService.PART_CATEGORY_LABELS, part.category),
            BOMService._label_or_raw(BOMService.MAIN_CATEGORY_LABELS, part.main_type),
            BOMService._label_or_raw(BOMService.SUB_CATEGORY_LABELS, part.sub_type),
        )

    @staticmethod
    def _split_export_main_category(value: str) -> Tuple[str, str]:
        text = str(value or '').strip()
        if '-' in text:
            first, second = text.split('-', 1)
            return first.strip(), second.strip()
        return text, ''

    @staticmethod
    def _label_or_raw(labels: Dict[str, str], value: Optional[str]) -> str:
        if not value:
            return ''
        return labels.get(str(value), str(value))

    @staticmethod
    def _normalize_header(value: Any) -> str:
        return re.sub(r'\s+', '', str(value or '').strip()).lower()

    @staticmethod
    def _clean_excel_cell(value: Any) -> str:
        if value is None:
            return ''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    @staticmethod
    def _clean_excel_version(value: Any, four_digit: bool = False) -> str:
        text = BOMService._clean_excel_cell(value)
        if not text:
            return ''
        if re.fullmatch(r'\d{1,4}', text):
            text = text.zfill(4)
        if four_digit and not re.fullmatch(r'\d{4}', text):
            raise ValueError(f"版本号必须是四位数字，例如 0001，当前值：{text}")
        return text

    @staticmethod
    def _normalize_bom_version(value: Any, default: str = '0001') -> str:
        text = BOMService._clean_excel_version(value)
        if not text:
            return default
        if not re.fullmatch(r'\d{4}', text):
            raise ValueError(f"BOM版本号必须是四位数字，例如 0001，当前值：{text}")
        return text

    @staticmethod
    def _find_part_version_by_no(part_id: str, version_no: str) -> Optional[VisirayPartNumberVersion]:
        version_text = BOMService._clean_excel_version(version_no, four_digit=True)
        return VisirayPartNumberVersion.query.filter_by(
            part_id=part_id,
            version_no=version_text,
        ).first()

    @staticmethod
    def _part_version_no(part_version_id: Optional[int]) -> str:
        if not part_version_id:
            return ''
        version = VisirayPartNumberVersion.query.get(part_version_id)
        return version.version_no if version else ''

    @staticmethod
    def _normalize_imported_part_categories(
        category: Any,
        main_category: Any,
        sub_category_group: Any,
        sub_category: Any,
    ) -> Tuple[str, str, str]:
        """将Excel中的当前分类名称转换为part_number表中的分类字段。

        老零件号与当前分类已经解耦，导入时类别只取Excel提供的值。
        允许Excel填写系统编码、显示名称或未配置的新名称；未识别的名称原样保存。
        """

        def clean(value: Any) -> str:
            return re.sub(r'\s+', '', BOMService._clean_excel_cell(value))

        def reverse_label(labels: Dict[str, str], value: Any) -> str:
            text = clean(value)
            if not text:
                return ''
            if text in labels:
                return text
            for key, label in labels.items():
                if clean(label) == text:
                    return key
            return text

        category_value = reverse_label(BOMService.PART_CATEGORY_LABELS, category)
        main_text = clean(main_category)
        sub_group_text = clean(sub_category_group)
        sub_value = reverse_label(BOMService.SUB_CATEGORY_LABELS, sub_category)

        # 中类别在导出文件中拆成“中类别-1”和“中类别-2”，数据库仍保存一个main_type。
        main_value = reverse_label(BOMService.MAIN_CATEGORY_LABELS, main_text)
        group_value = sub_group_text
        if group_value:
            group_value = reverse_label(BOMService.MAIN_CATEGORY_LABELS, group_value)

        if main_text and sub_group_text:
            combined_text = f"{main_text}-{sub_group_text}"
            combined_value = reverse_label(BOMService.MAIN_CATEGORY_LABELS, combined_text)
            if combined_value not in BOMService.MAIN_CATEGORY_LABELS and combined_text not in BOMService.MAIN_CATEGORY_LABELS.values():
                # 兼容“结构件 / 机加工”“光学件 / 透镜”等拆分后的当前分类。
                for key, label in BOMService.MAIN_CATEGORY_LABELS.items():
                    label_parts = [clean(part) for part in str(label).split('-', 1)]
                    if len(label_parts) == 2 and label_parts == [main_text, sub_group_text]:
                        combined_value = key
                        break
            main_value = combined_value
        elif not main_value and group_value:
            main_value = group_value

        return category_value, main_value, sub_value

    @staticmethod
    def _normalize_import_item_type(value: Any) -> Optional[str]:
        text = BOMService._clean_excel_cell(value).lower()
        if text in {'零件', 'part', 'material', '物料'}:
            return 'part'
        if text in {'子bom', 'bom', 'subbom', 'sub_bom', '子bOM'.lower()}:
            return 'sub_bom'
        return None

    @staticmethod
    def _parse_yes_no(value: Any) -> bool:
        text = BOMService._clean_excel_cell(value).lower()
        return text in {'是', 'yes', 'y', 'true', '1', '可选'}

    @staticmethod
    def _sort_key(value: Any) -> Tuple[int, Any]:
        text = BOMService._clean_excel_cell(value)
        if text.isdigit():
            return (0, int(text))
        return (1, text)

    @staticmethod
    def _format_import_errors(errors: List[Dict[str, Any]]) -> str:
        messages = []
        for item in errors[:20]:
            location = ''
            if item.get('sheet') and item.get('row'):
                location = f"{item['sheet']} 第{item['row']}行："
            messages.append(f"{location}{item.get('message')}")
        suffix = f"\n还有 {len(errors) - 20} 个错误未显示" if len(errors) > 20 else ''
        return "BOM导入失败：\n" + "\n".join(messages) + suffix

    @staticmethod
    def _collect_bom_requirements(
        bom: BOM,
        production_quantity: float,
        visited: Optional[set] = None,
        path: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        visited = set(visited or [])
        if bom.id in visited:
            return {}
        visited.add(bom.id)

        base_quantity = BOMService._to_float(bom.base_quantity, default=1.0) or 1.0
        scale = production_quantity / base_quantity
        path = list(path or [bom.bom_code])

        root_items = (
            bom.bom_items
            .filter(BOMItem.parent_item_id.is_(None))
            .order_by(BOMItem.sort_order, BOMItem.id)
            .all()
        )
        if not root_items:
            root_items = bom.bom_items.order_by(BOMItem.sort_order, BOMItem.id).all()

        result: Dict[str, Dict[str, Any]] = {}
        for item in root_items:
            BOMService._collect_item_requirements(
                item=item,
                parent_multiplier=scale,
                visited=visited.copy(),
                path=path,
                result=result,
            )
        return result

    @staticmethod
    def _get_active_bom(bom_id: int) -> Optional[BOM]:
        bom = BOM.query.get(bom_id)
        if not bom or bom.is_deleted:
            return None
        return bom

    @staticmethod
    def _collect_item_requirements(
        item: BOMItem,
        parent_multiplier: float,
        visited: set,
        path: List[str],
        result: Dict[str, Dict[str, Any]],
    ) -> None:
        usage_rate = BOMService._to_float(item.usage_rate, default=1.0) or 1.0
        item_multiplier = parent_multiplier * BOMService._to_float(item.quantity) * usage_rate
        item_label = item.material.material_name if item.material else item.sub_bom.bom_code if item.sub_bom else str(item.id)
        item_path = path + [item_label]

        if item.material:
            part_id = BOMService._material_part_id(item.material)
            version_id = getattr(item, 'part_version_id', None)
            key = f"part:{part_id}:version:{version_id}" if part_id else f"material:{item.material_id}"
            version = VisirayPartNumberVersion.query.get(version_id) if version_id else None
            current = result.setdefault(key, {
                'material_id': item.material_id,
                'material_code': part_id or item.material.material_code,
                'part_id': part_id,
                'part_version_id': version_id,
                'version_no': version.version_no if version else None,
                'material_name': item.material.material_name,
                'unit': item.unit or item.material.unit,
                'required_quantity': 0.0,
                'material_current_stock': BOMService._to_float(item.material.current_stock),
                'is_key_material': False,
                'is_optional': False,
                'substitute_group': item.substitute_group,
                'substitute_priority': item.substitute_priority,
                'paths': [],
            })
            current['required_quantity'] += item_multiplier
            current['is_key_material'] = current['is_key_material'] or bool(item.is_key_material)
            current['is_optional'] = current['is_optional'] or bool(item.is_optional)
            if item.substitute_group and not current.get('substitute_group'):
                current['substitute_group'] = item.substitute_group
            if item.substitute_priority and not current.get('substitute_priority'):
                current['substitute_priority'] = item.substitute_priority
            current['paths'].append(' > '.join(item_path))

        if item.sub_bom:
            nested = BOMService._collect_bom_requirements(
                bom=item.sub_bom,
                production_quantity=item_multiplier,
                visited=visited.copy(),
                path=item_path,
            )
            BOMService._merge_requirements(result, nested)

        children = sorted(
            list(item.child_items or []),
            key=lambda child: ((child.sort_order or 0), child.id or 0),
        )
        for child in children:
            BOMService._collect_item_requirements(
                item=child,
                parent_multiplier=item_multiplier,
                visited=visited.copy(),
                path=item_path,
                result=result,
            )

    @staticmethod
    def _merge_requirements(target: Dict[str, Dict[str, Any]], source: Dict[str, Dict[str, Any]]) -> None:
        for key, item in source.items():
            if key not in target:
                target[key] = item
                continue
            target_item = target[key]
            target_item['required_quantity'] += item.get('required_quantity', 0.0)
            target_item['is_key_material'] = target_item.get('is_key_material') or item.get('is_key_material')
            target_item['is_optional'] = target_item.get('is_optional') or item.get('is_optional')
            target_item.setdefault('paths', []).extend(item.get('paths') or [])

    @staticmethod
    def _material_part_id(material: Material) -> Optional[str]:
        if material.visiray_part_id:
            return material.visiray_part_id
        if material.remark and material.remark.startswith('VISIRAY_PART_ID:'):
            return material.remark.split(':', 1)[1]
        return None

    @staticmethod
    def _inventory_key(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        text = str(value).strip()
        upper = text.upper()
        for prefix in ('VSR4', 'VISB'):
            if upper.startswith(prefix):
                text = text[len(prefix):]
                break
        digits = re.sub(r'\D', '', text)
        return int(digits) if digits else None

    @staticmethod
    def _load_inventory_by_part_id(part_ids: List[str]) -> Dict[int, VisirayInventory]:
        return BOMService._load_inventory_by_part_and_version([(part_id, None) for part_id in part_ids])

    @staticmethod
    def _load_inventory_by_part_and_version(pairs: List[Tuple[Optional[str], Optional[int]]]) -> Dict[Tuple[int, Optional[int]], Any]:
        keys = []
        for part_id, version_id in pairs:
            inventory_key = BOMService._inventory_key(part_id)
            if inventory_key is not None:
                keys.append((inventory_key, version_id))
        if not keys:
            return {}

        part_keys = list({item[0] for item in keys})
        version_ids = list({item[1] for item in keys if item[1] is not None})
        records = VisirayVersionInventory.query.filter(VisirayVersionInventory.goods_id.in_(part_keys))
        if version_ids:
            records = records.filter(
                (VisirayVersionInventory.part_version_id.in_(version_ids)) |
                (VisirayVersionInventory.part_version_id.is_(None))
            )
        records = records.all()
        result = {}
        for record in records:
            result[(record.goods_id, record.part_version_id)] = record
        return result

    @staticmethod
    def _generate_bom_code(product_name: str) -> str:
        prefix = 'BOM'
        if product_name:
            name_prefix = ''.join(c.upper() for c in product_name if c.isalnum())[:3]
            if name_prefix:
                prefix = f"BOM{name_prefix}"
        return generate_code(prefix, 6)

    @staticmethod
    def _next_bom_version(version: Optional[str]) -> str:
        text = str(version or '').strip()
        if re.fullmatch(r'\d{1,4}', text):
            current = int(text)
        elif re.fullmatch(r'\d+(?:\.\d+)?', text):
            current = int(Decimal(text))
        else:
            current = 0

        next_value = current + 1
        if next_value > 9999:
            raise ValueError("BOM版本号已超过9999，无法自动升级")
        return str(next_value).zfill(4)

    @staticmethod
    def _generate_upgraded_bom_code(source_code: str, version: str) -> str:
        version_suffix = re.sub(r'[^A-Za-z0-9]+', '.', str(version or '').strip()).strip('.') or 'NEXT'
        base_code = f"{source_code}-V{version_suffix}"[:32]
        if not BOM.query.filter_by(bom_code=base_code).first():
            return base_code

        for index in range(2, 100):
            suffix = f"-{index}"
            code = f"{base_code[:32 - len(suffix)]}{suffix}"
            if not BOM.query.filter_by(bom_code=code).first():
                return code

        return BOMService._generate_bom_code(source_code)

    @staticmethod
    def _recalculate_referencing_boms(changed_bom_id: int, visited: Optional[set] = None) -> None:
        visited = set(visited or [])
        if changed_bom_id in visited:
            return
        visited.add(changed_bom_id)

        parent_bom_ids = {
            item.bom_id
            for item in BOMItem.query.filter_by(sub_bom_id=changed_bom_id).all()
            if item.bom_id and item.bom_id not in visited
        }
        for parent_bom_id in parent_bom_ids:
            parent_bom = BOM.query.get(parent_bom_id)
            if not parent_bom:
                continue
            try:
                parent_bom.calculate_cost()
            except Exception as e:
                current_app.logger.warning(f"Recalculate parent BOM cost failed for BOM {parent_bom.id}: {e}")
                continue
            db.session.flush()
            BOMService._recalculate_referencing_boms(parent_bom.id, visited.copy())

    @staticmethod
    def _recalculate_bom_and_references(bom_id: int) -> None:
        """Recalculate one BOM and every parent BOM that references it as a sub BOM."""
        db.session.flush()
        db.session.expire_all()

        bom = BOM.query.get(bom_id)
        if not bom:
            return
        bom.calculate_cost()
        db.session.flush()
        db.session.expire_all()
        BOMService._recalculate_referencing_boms(bom_id)

    @staticmethod
    def _replace_bom_items(
        bom_id: int,
        items_data: List[Dict[str, Any]],
        created_by: Optional[int] = None,
        allow_existing_inactive_sub_boms: bool = False,
    ) -> None:
        existing_items = (
            BOMItem.query.filter_by(bom_id=bom_id)
            .order_by(BOMItem.level.desc(), BOMItem.id.desc())
            .all()
        )
        existing_sub_bom_ids = {
            int(item.sub_bom_id)
            for item in existing_items
            if item.sub_bom_id
        }
        for item in existing_items:
            db.session.delete(item)
        db.session.flush()

        flat_items = BOMService._flatten_items(items_data)
        created_by_client_id: Dict[str, BOMItem] = {}
        pending_parent_links: List[Tuple[BOMItem, Optional[str]]] = []

        for index, (item_data, parent_client_id, level) in enumerate(flat_items):
            item = BOMService._build_bom_item(
                bom_id=bom_id,
                item_data=item_data,
                created_by=created_by,
                level=level,
                sort_order=item_data.get('sort_order', index + 1),
                allowed_inactive_sub_bom_ids=(
                    existing_sub_bom_ids
                    if allow_existing_inactive_sub_boms
                    else None
                ),
            )
            db.session.add(item)

            client_id = BOMService._client_id(item_data)
            if client_id:
                created_by_client_id[client_id] = item
            pending_parent_links.append((item, parent_client_id))

        db.session.flush()

        for item, parent_client_id in pending_parent_links:
            if parent_client_id:
                parent_item = created_by_client_id.get(parent_client_id)
                if not parent_item:
                    raise ValueError("BOM item parent reference is invalid")
                item.parent_item_id = parent_item.id

        db.session.flush()

    @staticmethod
    def _flatten_items(
        items_data: List[Dict[str, Any]],
        parent_client_id: Optional[str] = None,
        level: int = 1,
    ) -> List[Tuple[Dict[str, Any], Optional[str], int]]:
        if level > 3:
            raise ValueError("BOM最多支持四级结构：整机 -> 模块 -> 子组件 -> 零件")

        flat: List[Tuple[Dict[str, Any], Optional[str], int]] = []
        for index, item_data in enumerate(items_data):
            if not item_data.get('material_id') and not item_data.get('part_id') and not item_data.get('sub_bom_id'):
                raise ValueError("Each BOM item must reference a part number, material, or sub BOM")
            if not item_data.get('quantity'):
                raise ValueError("BOM item quantity is required")
            if level >= 3 and item_data.get('sub_bom_id'):
                raise ValueError("第三级明细必须选择零件号，不能再选择子BOM")

            item_copy = dict(item_data)
            item_copy['sort_order'] = item_data.get('sort_order', index + 1)
            item_client_id = BOMService._client_id(item_copy) or f"auto-{level}-{index}"
            item_copy['client_id'] = item_client_id
            flat.append((item_copy, parent_client_id, level))

            children = item_data.get('children') or []
            if children and level >= 3:
                raise ValueError("零件层不能继续添加子节点，BOM最多支持四级结构")
            flat.extend(BOMService._flatten_items(children, item_client_id, level + 1))

        return flat

    @staticmethod
    def _build_bom_item(
        bom_id: int,
        item_data: Dict[str, Any],
        created_by: Optional[int],
        level: int,
        sort_order: int,
        allowed_inactive_sub_bom_ids: Optional[Set[int]] = None,
    ) -> BOMItem:
        sub_bom_id = item_data.get('sub_bom_id')
        if sub_bom_id and int(sub_bom_id) == int(bom_id):
            raise ValueError("BOM cannot reference itself as a sub BOM")
        if sub_bom_id:
            sub_bom = BOM.query.get(sub_bom_id)
            if not sub_bom:
                raise ValueError("子BOM不存在")
            allowed_existing = (
                allowed_inactive_sub_bom_ids is not None
                and int(sub_bom_id) in allowed_inactive_sub_bom_ids
            )
            if sub_bom.status != 'active' and not allowed_existing:
                raise ValueError("只有生效状态的BOM才能作为子模块使用")

        material_id = item_data.get('material_id') or None
        part_version_id = item_data.get('part_version_id')
        if item_data.get('part_id'):
            part = VisirayPartNumber.query.get(str(item_data['part_id']).strip())
            if not part:
                raise ValueError("零件号不存在")
            part_version_id = BOMService._resolve_bom_part_version(part, part_version_id)
            material_id = BOMService._get_or_create_material_from_part(item_data['part_id'], created_by)
        selected_supplier = BOMService._resolve_selected_supplier(material_id, item_data.get('selected_supplier_id'), part_version_id)

        return BOMItem(
            bom_id=bom_id,
            material_id=material_id,
            part_version_id=part_version_id,
            sub_bom_id=sub_bom_id or None,
            parent_item_id=None,
            level=level,
            sort_order=sort_order,
            item_no=item_data.get('item_no'),
            quantity=BOMService._to_float(item_data['quantity'], default=0.0),
            unit=item_data.get('unit'),
            is_key_material=item_data.get('is_key_material', False),
            is_optional=item_data.get('is_optional', False),
            usage_rate=BOMService._to_float(item_data.get('usage_rate', 1.0), default=1.0),
            selected_supplier_id=getattr(selected_supplier, 'id', None),
            selected_supplier_price=getattr(selected_supplier, 'price', None),
            substitute_group=item_data.get('substitute_group'),
            substitute_priority=item_data.get('substitute_priority', 1),
            process_step=item_data.get('process_step'),
            assembly_note=item_data.get('assembly_note'),
            effective_date=BOMService._parse_datetime(item_data.get('effective_date')),
            expiry_date=BOMService._parse_datetime(item_data.get('expiry_date')),
            remark=item_data.get('remark'),
        )

    @staticmethod
    def _resolve_bom_part_version(part: VisirayPartNumber, part_version_id=None) -> Optional[int]:
        versions = VisirayPartNumberVersion.query.filter_by(part_id=part.part_id).order_by(
            VisirayPartNumberVersion.created_at.desc(),
            VisirayPartNumberVersion.id.desc(),
        ).all()
        if part_version_id in (None, ''):
            if not versions:
                return None
            current = next(
                (version for version in versions if version.is_current and version.status == 'active'),
                None,
            )
            current = current or next(
                (version for version in versions if version.status == 'active'),
                None,
            )
            if not current:
                raise ValueError("该零件号没有可用于BOM的有效版本")
            return current.id

        try:
            version_id = int(part_version_id)
        except (TypeError, ValueError):
            raise ValueError("零件版本无效")
        version = VisirayPartNumberVersion.query.get(version_id)
        if not version or version.part_id != part.part_id:
            raise ValueError("零件版本不属于当前零件号")
        if version.status != 'active':
            raise ValueError("废弃版本不能加入新BOM")
        return version.id

    @staticmethod
    def _get_or_create_material_from_part(part_id: str, created_by: Optional[int]) -> int:
        part_key = str(part_id).strip()
        if not part_key:
            raise ValueError("Part number is required")

        part = VisirayPartNumber.query.get(part_key)
        if not part:
            raise ValueError(f"Part number {part_key} does not exist")

        marker = BOMService._part_material_marker(part.part_id)
        material = Material.query.filter_by(visiray_part_id=part.part_id).first()
        if not material:
            material = Material.query.filter_by(remark=marker).first()
        if material:
            material.visiray_part_id = part.part_id
            material.material_name = part.part_name or part.sub_type or part.part_id
            material.specification = ' / '.join(filter(None, [part.category, part.main_type, part.sub_type]))
            material.unit = part.unit or material.unit or 'pcs'
            material.standard_cost = BOMService._to_float(getattr(part, 'standard_cost', None), default=0.0)
            material.remark = marker
            return material.id

        material = Material(
            material_code=BOMService._generate_part_material_code(),
            visiray_part_id=part.part_id,
            material_name=part.part_name or part.sub_type or part.part_id,
            specification=' / '.join(filter(None, [part.category, part.main_type, part.sub_type])),
            unit=part.unit or 'pcs',
            standard_cost=BOMService._to_float(getattr(part, 'standard_cost', None), default=0.0),
            currency='CNY',
            material_type='custom',
            status='active',
            created_by=created_by,
            remark=marker,
        )
        material.parse_material_code()
        db.session.add(material)
        db.session.flush()
        return material.id

    @staticmethod
    def _resolve_selected_supplier(material_id: Optional[int], selected_supplier_id: Optional[int], part_version_id: Optional[int] = None) -> Optional[MaterialSupplier]:
        if not material_id:
            return None

        if selected_supplier_id:
            supplier = MaterialSupplier.query.get(selected_supplier_id)
            if not supplier or supplier.status != 'active':
                raise ValueError("供应商报价不存在或已停用")
            if int(supplier.material_id) != int(material_id):
                raise ValueError("供应商报价不属于当前零件")
            if part_version_id is not None and supplier.part_version_id not in (None, part_version_id):
                raise ValueError("供应商报价版本不匹配")
            return supplier

        query = MaterialSupplier.query.filter_by(material_id=material_id, status='active')
        if part_version_id is not None:
            exact = query.filter_by(part_version_id=part_version_id).order_by(
                MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc()
            ).all()
            generic = query.filter(MaterialSupplier.part_version_id.is_(None)).order_by(
                MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc()
            ).all()
            candidates = exact + generic
        else:
            candidates = query.filter(MaterialSupplier.part_version_id.is_(None)).order_by(
                MaterialSupplier.is_primary.desc(), MaterialSupplier.id.asc()
            ).all()
        return candidates[0] if candidates else None

    @staticmethod
    def _generate_part_material_code() -> str:
        for classification in range(0, 100):
            code = MaterialCodeService.generate_material_code(
                part_type='custom',
                material_type='custom',
                part_category='mechanical',
                classification=classification,
                version=0,
            )
            if not Material.query.filter_by(material_code=code).first():
                return code
        raise ValueError("Unable to generate material code for part number")

    @staticmethod
    def _part_material_marker(part_id: str) -> str:
        return f"VISIRAY_PART_ID:{part_id}"

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value is None or value == '':
            return default
        return float(value)

    @staticmethod
    def _client_id(item_data: Dict[str, Any]) -> Optional[str]:
        value = (
            item_data.get('client_id')
            or item_data.get('temp_id')
            or item_data.get('key')
            or item_data.get('id')
        )
        return str(value) if value is not None else None

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))

    @staticmethod
    def _normalize_status(value: Optional[str]) -> str:
        status_map = {
            'draft': 'draft',
            '草稿': 'draft',
            'active': 'active',
            '生效': 'active',
            'inactive': 'inactive',
            '停用': 'inactive',
            'obsolete': 'obsolete',
            '作废': 'obsolete',
        }
        normalized = status_map.get(str(value or 'draft').strip())
        if not normalized:
            raise ValueError("BOM状态必须是草稿、生效、停用或作废")
        return normalized







