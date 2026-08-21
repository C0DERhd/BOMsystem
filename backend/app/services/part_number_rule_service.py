import copy
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.models.visiray import VisirayPartNumber, VisirayPartNumberRule


FINAL_RULE_STANDARD = "vsr_final_20260807"

TERTIARY_KEYS = [
    "material_aluminum",
    "material_plastic",
    "material_steel",
    "material_glass",
    "material_other",
    "surface_sandblast",
    "surface_anodized",
    "surface_spray",
    "surface_sandblast_anodized",
]

SECONDARY_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "processed_structure_machining": {"name": "结构件-机加工", "code": "1110", "parent_key": "processed"},
    "processed_structure_3d_printing": {"name": "结构件-3D打印", "code": "1111", "parent_key": "processed"},
    "processed_structure_sheet_metal": {"name": "结构件-折弯钣金", "code": "1112", "parent_key": "processed"},
    "processed_structure_molding": {"name": "结构件-成型", "code": "1113", "parent_key": "processed"},
    "processed_structure_standard_rework": {"name": "结构件-标准件再加工", "code": "1114", "parent_key": "processed"},
    "processed_optical_mirror": {"name": "光学件-反光镜", "code": "1220", "parent_key": "processed"},
    "processed_optical_lens": {"name": "光学件-透镜", "code": "1221", "parent_key": "processed"},
    "processed_optical_prism": {"name": "光学件-棱镜", "code": "1222", "parent_key": "processed"},
    "processed_optical_beamsplitter": {"name": "光学件-分光镜", "code": "1223", "parent_key": "processed"},
    "processed_optical_filter": {"name": "光学件-滤光片", "code": "1224", "parent_key": "processed"},
    "processed_electrical_pba": {"name": "电气件-PBA", "code": "1330", "parent_key": "processed"},
    "processed_electrical_wire": {"name": "电气件-线材", "code": "1331", "parent_key": "processed"},
    "processed_other": {"name": "其它", "code": "1444", "parent_key": "processed"},
    "custom_part": {"name": "零件", "code": "2100", "parent_key": "custom"},
    "custom_product": {"name": "产品", "code": "2200", "parent_key": "custom"},
    "standard_mechanical": {"name": "机械类", "code": "3100", "parent_key": "standard"},
    "standard_optical": {"name": "光学类", "code": "3200", "parent_key": "standard"},
    "standard_electrical": {"name": "电气类", "code": "3300", "parent_key": "standard"},
    "fastener_screw": {"name": "螺丝类", "code": "4100", "parent_key": "fastener"},
    "fastener_nut": {"name": "螺母类", "code": "4200", "parent_key": "fastener"},
    "fastener_washer": {"name": "垫片类", "code": "4300", "parent_key": "fastener"},
    "fastener_spring": {"name": "弹簧类", "code": "4400", "parent_key": "fastener"},
    "fastener_pin": {"name": "销钉类", "code": "4500", "parent_key": "fastener"},
    "fastener_clip": {"name": "线卡类", "code": "4600", "parent_key": "fastener"},
    "chemical_developer": {"name": "显影类", "code": "5100", "parent_key": "chemical"},
    "chemical_etching": {"name": "刻蚀类", "code": "5200", "parent_key": "chemical"},
    "chemical_adhesive": {"name": "胶水类", "code": "5300", "parent_key": "chemical", "description": "螺纹胶，AB胶，结构胶等"},
    "chemical_cleaning": {"name": "清洗类", "code": "5400", "parent_key": "chemical", "description": "酒精，洗板水等"},
    "chemical_photosensitive_ink": {"name": "感光油墨", "code": "5500", "parent_key": "chemical", "description": "绿油，蓝油等"},
    "tooling_default": {"name": "工装", "code": "6000", "parent_key": "tooling"},
    "consumable_default": {"name": "辅助材料/耗材", "code": "7000", "parent_key": "consumable"},
    "software_default": {"name": "软件", "code": "8000", "parent_key": "software"},
    "product_bom_default": {"name": "产品BOM", "code": "9000", "parent_key": "product_bom"},
}


DEFAULT_PART_NUMBER_RULE_CONFIG: Dict[str, Any] = {
    "rule_standard": FINAL_RULE_STANDARD,
    "code_length": 12,
    "sequence_start": 1,
    "sequence_scope": "part_category_code",
    "segments": [
        {
            "key": "primary_category",
            "name": "一级编码（大类）",
            "length": 2,
            "source": "part_category_code",
            "description": "10=加工件，20=定制件，30=标准件，40=紧固件，50=化学品，60=工装，70=辅助材料/耗材，80=软件，90=产品BOM",
        },
        {
            "key": "secondary_category",
            "name": "二级编码（次级类别）",
            "length": 4,
            "source": "main_category_code",
            "description": "四位数字；只有两位分类时后两位默认为00",
        },
        {
            "key": "tertiary_code",
            "name": "三级编码（材质及表面处理）",
            "length": 2,
            "source": "sub_category_index",
            "description": "10/20/30/40/50为材质，60/70/80/90为表面处理",
        },
        {
            "key": "sequence",
            "name": "四级编码（产品/零件流水号）",
            "length": 4,
            "source": "sequence",
            "description": "按一级大类分别从0001开始流水",
        },
    ],
    "part_categories": {
        "processed": {"name": "加工件", "code": "10", "description": "需要加工的零部件"},
        "custom": {"name": "定制件", "code": "20", "description": "定制化的零件或产品"},
        "standard": {"name": "标准件", "code": "30", "description": "可以直接采购的零部件"},
        "fastener": {"name": "紧固件", "code": "40", "description": "起锁紧目的且可直接采购的零部件"},
        "chemical": {"name": "化学品", "code": "50", "description": ""},
        "tooling": {"name": "工装", "code": "60", "description": "只是生产过程中使用"},
        "consumable": {"name": "辅助材料/耗材", "code": "70", "description": "胶水，酒精，清洁纸，PCB等"},
        "software": {"name": "软件", "code": "80", "description": "主指可对外销售产品上的正式版本软件"},
        "product_bom": {"name": "产品BOM", "code": "90", "description": "对外销售的产品"},
    },
    "main_categories": SECONDARY_CATEGORIES,
    "sub_categories": {
        "material_aluminum": {"name": "铝", "code": "10", "group": "材质"},
        "material_plastic": {"name": "塑料", "code": "20", "group": "材质"},
        "material_steel": {"name": "钢", "code": "30", "group": "材质"},
        "material_glass": {"name": "玻璃", "code": "40", "group": "材质"},
        "material_other": {"name": "其它", "code": "50", "group": "材质"},
        "surface_sandblast": {"name": "喷砂", "code": "60", "group": "表面处理"},
        "surface_anodized": {"name": "阳极氧化", "code": "70", "group": "表面处理"},
        "surface_spray": {"name": "喷涂", "code": "80", "group": "表面处理"},
        "surface_sandblast_anodized": {"name": "喷砂+阳极氧化", "code": "90", "group": "表面处理"},
    },
    "sub_category_orders": {key: list(TERTIARY_KEYS) for key in SECONDARY_CATEGORIES.keys()},
}


class PartNumberRuleService:
    @staticmethod
    def default_config() -> Dict[str, Any]:
        return copy.deepcopy(DEFAULT_PART_NUMBER_RULE_CONFIG)

    @classmethod
    def ensure_default_rule(cls) -> VisirayPartNumberRule:
        rules = VisirayPartNumberRule.query.order_by(VisirayPartNumberRule.id.asc()).all()
        active = next((rule for rule in rules if rule.is_active), None)
        final_rule = next(
            (rule for rule in rules if (rule.get_config() or {}).get("rule_standard") == FINAL_RULE_STANDARD),
            None,
        )

        if final_rule:
            if not active:
                final_rule.is_active = True
                db.session.flush()
                return final_rule
            return active

        VisirayPartNumberRule.query.update({VisirayPartNumberRule.is_active: False})
        rule = VisirayPartNumberRule(
            rule_name="VSR最终版12位零件号规则",
            prefix="VSR",
            is_active=True,
            remark="系统内置默认规则，来自《编码规则.docx》最终版。",
        )
        rule.set_config(cls.default_config())
        db.session.add(rule)
        db.session.flush()
        return rule

    @classmethod
    def get_active_rule(cls) -> VisirayPartNumberRule:
        return cls.ensure_default_rule()

    @classmethod
    def list_rules(cls) -> List[VisirayPartNumberRule]:
        cls.ensure_default_rule()
        return VisirayPartNumberRule.query.order_by(
            VisirayPartNumberRule.is_active.desc(),
            VisirayPartNumberRule.updated_at.desc(),
            VisirayPartNumberRule.id.desc(),
        ).all()

    @classmethod
    def create_rule(cls, data: Dict[str, Any], user_id=None) -> VisirayPartNumberRule:
        config = data.get("config") or cls.default_config()
        cls.validate_config(config)
        rule = VisirayPartNumberRule(
            rule_name=(data.get("rule_name") or "零件号规则").strip(),
            prefix=(data.get("prefix") or "").strip(),
            remark=data.get("remark"),
            created_by=user_id,
            updated_by=user_id,
            is_active=bool(data.get("is_active")),
        )
        rule.set_config(config)
        if rule.is_active:
            VisirayPartNumberRule.query.update({VisirayPartNumberRule.is_active: False})
        db.session.add(rule)
        db.session.flush()
        return rule

    @classmethod
    def update_rule(cls, rule_id: int, data: Dict[str, Any], user_id=None) -> VisirayPartNumberRule:
        rule = VisirayPartNumberRule.query.get(rule_id)
        if not rule:
            raise ValueError("规则不存在")

        if "config" in data:
            cls.validate_config(data.get("config") or {})
            rule.set_config(data.get("config") or {})
        if "rule_name" in data:
            rule.rule_name = (data.get("rule_name") or "零件号规则").strip()
        if "prefix" in data:
            rule.prefix = (data.get("prefix") or "").strip()
        if "remark" in data:
            rule.remark = data.get("remark")
        rule.updated_by = user_id
        db.session.flush()
        return rule

    @classmethod
    def activate_rule(cls, rule_id: int, user_id=None) -> VisirayPartNumberRule:
        rule = VisirayPartNumberRule.query.get(rule_id)
        if not rule:
            raise ValueError("规则不存在")
        cls.validate_config(rule.get_config())
        VisirayPartNumberRule.query.update({VisirayPartNumberRule.is_active: False})
        rule.is_active = True
        rule.updated_by = user_id
        db.session.flush()
        return rule

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(config, dict):
            raise ValueError("规则配置必须是对象")
        segments = config.get("segments")
        if not isinstance(segments, list) or not segments:
            raise ValueError("规则配置必须包含编码段")
        if not any(segment.get("source") == "sequence" for segment in segments):
            raise ValueError("规则配置必须包含流水号段")

        total_length = 0
        for segment in segments:
            length = int(segment.get("length") or 0)
            if length <= 0:
                raise ValueError("编码段长度必须大于0")
            if not segment.get("key"):
                raise ValueError("编码段必须包含key")
            total_length += length

        code_length = int(config.get("code_length") or total_length)
        if total_length != code_length:
            raise ValueError(f"编码段长度合计为{total_length}，与规则总长度{code_length}不一致")
        return True, "规则有效"

    @classmethod
    def generate_part_number(cls, data: Dict[str, Any], reserved_numbers=None) -> str:
        rule = cls.get_active_rule()
        config = rule.get_config()
        cls.validate_config(config)

        segments = config.get("segments") or []
        sequence_segment = next(segment for segment in segments if segment.get("source") == "sequence")
        sequence_length = int(sequence_segment.get("length"))
        max_sequence = (10 ** sequence_length) - 1
        start_sequence = int(config.get("sequence_start") or 0)

        reserved_numbers = reserved_numbers or set()
        for sequence in range(start_sequence, max_sequence + 1):
            body = cls._build_body(config, data, sequence)
            part_number = f"{rule.prefix or ''}{body}"
            if part_number in reserved_numbers:
                continue
            if VisirayPartNumber.query.get(part_number) is not None:
                continue
            if cls._sequence_used_in_scope(config, rule.prefix or "", body, reserved_numbers):
                continue
            return part_number
        raise ValueError("无法生成新的零件号：当前规则的流水号范围已用完")

    @classmethod
    def generate_next_version_part_number(cls, current_part_number: str, reserved_numbers=None) -> str:
        raise ValueError("生成新版零件号功能已停用，请通过供应商报价管理价格差异")

    @classmethod
    def _build_body(cls, config: Dict[str, Any], data: Dict[str, Any], sequence: int) -> str:
        parts = []
        for segment in config.get("segments") or []:
            value = cls._resolve_segment_value(config, segment, data, sequence)
            length = int(segment.get("length"))
            value = str(value or "")
            if len(value) > length:
                raise ValueError(f"{segment.get('name') or segment.get('key')} 的编码长度超过{length}位")
            parts.append(value.zfill(length))
        return "".join(parts)

    @classmethod
    def _resolve_segment_value(
        cls,
        config: Dict[str, Any],
        segment: Dict[str, Any],
        data: Dict[str, Any],
        sequence: int,
    ) -> str:
        source = segment.get("source")
        part_category = data.get("partCategory") or data.get("part_category") or "custom"
        main_category = data.get("mainCategory") or data.get("main_category") or ""
        sub_category = data.get("subCategory") or data.get("sub_category") or ""

        if source == "static":
            return str(segment.get("value", ""))
        if source == "sequence":
            return str(sequence)
        if source == "part_category_code":
            return cls._lookup(config.get("part_categories"), part_category, "code", "20")
        if source == "part_category_identifier":
            return cls._lookup(config.get("part_categories"), part_category, "identifier", "")
        if source == "main_category_code":
            return cls._lookup(config.get("main_categories"), main_category, "code", "2100")
        if source == "sub_category_index":
            return str(cls._sub_category_code(config, main_category, sub_category))
        return str(segment.get("value", ""))

    @staticmethod
    def _lookup(mapping: Optional[Dict[str, Any]], key: str, field: str, default: str) -> str:
        value = (mapping or {}).get(key) or {}
        return str(value.get(field, default))

    @staticmethod
    def _sub_category_code(config: Dict[str, Any], main_category: str, sub_category: str) -> int:
        sub_categories = config.get("sub_categories") or {}
        sub_info = sub_categories.get(sub_category) or {}
        if sub_info.get("code") is not None:
            return int(sub_info.get("code"))

        orders = config.get("sub_category_orders") or {}
        order = orders.get(main_category)
        if isinstance(order, list) and sub_category in order:
            return max(0, min(99, order.index(sub_category)))

        default_sub_info = (DEFAULT_PART_NUMBER_RULE_CONFIG.get("sub_categories") or {}).get(sub_category) or {}
        if default_sub_info.get("code") is not None:
            return int(default_sub_info.get("code"))
        return 0

    @staticmethod
    def _segment_positions(config: Dict[str, Any]) -> Dict[str, Tuple[int, int]]:
        cursor = 0
        positions: Dict[str, Tuple[int, int]] = {}
        for segment in config.get("segments") or []:
            length = int(segment.get("length") or 0)
            for key in (segment.get("source"), segment.get("key")):
                if key:
                    positions[str(key)] = (cursor, cursor + length)
            cursor += length
        return positions

    @classmethod
    def _sequence_used_in_scope(
        cls,
        config: Dict[str, Any],
        prefix: str,
        body: str,
        reserved_numbers,
    ) -> bool:
        if config.get("sequence_scope") != "part_category_code":
            return False

        positions = cls._segment_positions(config)
        category_pos = positions.get("part_category_code")
        sequence_pos = positions.get("sequence")
        if not category_pos or not sequence_pos:
            return False

        category_value = body[category_pos[0]:category_pos[1]]
        sequence_value = body[sequence_pos[0]:sequence_pos[1]]

        for part_number in reserved_numbers or set():
            candidate = cls._strip_prefix(str(part_number), prefix)
            if len(candidate) != len(body):
                continue
            if (
                candidate[category_pos[0]:category_pos[1]] == category_value
                and candidate[sequence_pos[0]:sequence_pos[1]] == sequence_value
            ):
                return True

        if category_pos[0] == 0:
            query = VisirayPartNumber.query.filter(VisirayPartNumber.part_id.like(f"{prefix}{category_value}%"))
        else:
            query = VisirayPartNumber.query

        for record in query.all():
            candidate = cls._strip_prefix(record.part_id, prefix)
            if len(candidate) != len(body):
                continue
            if (
                candidate[category_pos[0]:category_pos[1]] == category_value
                and candidate[sequence_pos[0]:sequence_pos[1]] == sequence_value
            ):
                return True
        return False

    @staticmethod
    def _strip_prefix(part_number: str, prefix: str) -> str:
        body = str(part_number or "")
        if prefix and body.startswith(prefix):
            return body[len(prefix):]
        for legacy_prefix in ("VSR4", "VISB"):
            if body.startswith(legacy_prefix):
                return body[len(legacy_prefix):]
        return body
