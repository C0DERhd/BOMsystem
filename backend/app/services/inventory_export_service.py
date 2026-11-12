from copy import copy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


class InventoryExportService:
    """Generate printable inbound and outbound forms from existing templates."""

    TEMPLATE_DIR = Path(__file__).resolve().parents[1] / 'templates' / 'exports'

    @staticmethod
    def _common_value(records, key, multiple_text='多个'):
        values = []
        for record in records:
            value = record.get(key)
            if value not in (None, '') and str(value) not in values:
                values.append(str(value))
        if not values:
            return ''
        return values[0] if len(values) == 1 else multiple_text

    @staticmethod
    def _model_text(record):
        product_model = str(record.get('product_model') or '').strip()
        version_no = str(record.get('version_no') or '').strip()
        if product_model and version_no and version_no not in product_model:
            return f'{product_model} / {version_no}'
        return product_model or version_no

    @staticmethod
    def _expand_detail_rows(sheet, template_detail_end, total_row, signature_row, record_count):
        extra_rows = max(0, record_count - 6)
        if not extra_rows:
            return total_row, signature_row

        shifted_merges = []
        for merged_range in list(sheet.merged_cells.ranges):
            if merged_range.min_row < total_row:
                continue
            sheet.unmerge_cells(str(merged_range))
            shifted_merges.append(
                f'{get_column_letter(merged_range.min_col)}{merged_range.min_row + extra_rows}:'
                f'{get_column_letter(merged_range.max_col)}{merged_range.max_row + extra_rows}'
            )

        sheet.insert_rows(total_row, amount=extra_rows)
        for merged_range in shifted_merges:
            sheet.merge_cells(merged_range)

        source_height = sheet.row_dimensions[template_detail_end].height
        for row_number in range(total_row, total_row + extra_rows):
            sheet.row_dimensions[row_number].height = source_height
            for column_number in range(1, 13):
                source = sheet.cell(template_detail_end, column_number)
                target = sheet.cell(row_number, column_number)
                if source.has_style:
                    target._style = copy(source._style)
            sheet.merge_cells(start_row=row_number, start_column=1, end_row=row_number, end_column=2)
            sheet.merge_cells(start_row=row_number, start_column=3, end_row=row_number, end_column=4)
            sheet.merge_cells(start_row=row_number, start_column=5, end_row=row_number, end_column=6)

        return total_row + extra_rows, signature_row + extra_rows

    @staticmethod
    def _add_inbound_detail_columns(sheet):
        original_merges = [str(rng) for rng in sheet.merged_cells.ranges]
        for merged_range in list(sheet.merged_cells.ranges):
            if merged_range.max_col >= 8:
                sheet.unmerge_cells(str(merged_range))

        sheet.insert_cols(8, amount=2)
        for merged_range in original_merges:
            start, end = merged_range.split(':')
            start_cell = sheet[start]
            end_cell = sheet[end]
            if end_cell.column >= 8:
                start_column = get_column_letter(start_cell.column + (2 if start_cell.column >= 8 else 0))
                end_column = get_column_letter(end_cell.column + 2)
                sheet.merge_cells(f'{start_column}{start_cell.row}:{end_column}{end_cell.row}')

        sheet.column_dimensions['H'].width = 13
        sheet.column_dimensions['I'].width = 18
        sheet.column_dimensions['J'].width = 13
        sheet.column_dimensions['K'].width = 14
        for row_number in range(6, sheet.max_row + 1):
            for source_column, target_column in ((10, 8), (11, 9)):
                source = sheet.cell(row_number, source_column)
                target = sheet.cell(row_number, target_column)
                if source.has_style:
                    target._style = copy(source._style)

    @staticmethod
    def _add_outbound_date_column(sheet):
        original_merges = [str(rng) for rng in sheet.merged_cells.ranges]
        for merged_range in list(sheet.merged_cells.ranges):
            if merged_range.max_col >= 8:
                sheet.unmerge_cells(str(merged_range))

        sheet.insert_cols(8, amount=3)
        for merged_range in original_merges:
            start, end = merged_range.split(':')
            start_cell = sheet[start]
            end_cell = sheet[end]
            if end_cell.column >= 8:
                start_column = get_column_letter(start_cell.column + (3 if start_cell.column >= 8 else 0))
                end_column = get_column_letter(end_cell.column + 3)
                sheet.merge_cells(f'{start_column}{start_cell.row}:{end_column}{end_cell.row}')

        sheet.column_dimensions['H'].width = 13
        sheet.column_dimensions['I'].width = 14
        sheet.column_dimensions['J'].width = 13
        sheet.column_dimensions['K'].width = 18
        sheet.column_dimensions['L'].width = 13
        for row_number in range(5, sheet.max_row + 1):
            source = sheet.cell(row_number, 11)
            for target_column in (8, 9, 10):
                target = sheet.cell(row_number, target_column)
                if source.has_style:
                    target._style = copy(source._style)

    @staticmethod
    def _fit_record_id(cell):
        alignment = copy(cell.alignment)
        alignment.wrap_text = False
        alignment.shrink_to_fit = True
        cell.alignment = alignment
        font = copy(cell.font)
        font.size = 8
        cell.font = font
        cell.number_format = '@'

    @staticmethod
    def _bold_labels(sheet, addresses):
        for address in addresses:
            font = copy(sheet[address].font)
            font.bold = True
            sheet[address].font = font

    @classmethod
    def export_inbound(cls, records):
        workbook = load_workbook(cls.TEMPLATE_DIR / 'inbound_template.xlsx')
        sheet = workbook.active
        sheet.title = '入库单'
        cls._add_inbound_detail_columns(sheet)
        total_row, signature_row = cls._expand_detail_rows(sheet, 12, 13, 14, len(records))

        sheet['A2'] = '制单日期'
        sheet['B2'] = datetime.now().date()
        sheet['B2'].number_format = 'yyyy-mm-dd'
        sheet['F2'] = cls._common_value(records, 'shelf_location', '多货架')
        shelf_alignment = copy(sheet['F2'].alignment)
        shelf_alignment.horizontal = 'left'
        sheet['F2'].alignment = shelf_alignment
        sheet['B3'] = cls._common_value(records, 'supplier_name', '多供应商')
        sheet['B4'] = cls._common_value(records, 'inbound_type', '多种入库') or '入库'

        sheet['B5'] = ''
        sheet.cell(signature_row, 2, '')

        sheet['H6'] = '入库时间'
        sheet['I6'] = '入库记录号'
        sheet['J6'] = '单价'
        sheet['K6'] = '总价'
        detail_columns = (1, 3, 5, 7, 8, 9, 10, 11)
        for column_number in detail_columns:
            header_alignment = copy(sheet.cell(6, column_number).alignment)
            header_alignment.horizontal = 'center'
            header_alignment.vertical = 'center'
            header_alignment.indent = 0
            sheet.cell(6, column_number).alignment = header_alignment

        for row_number, record in enumerate(records, start=7):
            sheet.cell(row_number, 1, record.get('display_goods_id') or record.get('goods_id') or '')
            sheet.cell(row_number, 3, record.get('goods_name') or '')
            model_cell = sheet.cell(row_number, 5, cls._model_text(record))
            model_cell.number_format = '@'
            sheet.cell(row_number, 7, record.get('quantity'))
            sheet.cell(row_number, 7).number_format = '0'
            date_cell = sheet.cell(row_number, 8, record.get('in_date') or '')
            date_cell.number_format = 'yyyy-mm-dd'
            record_cell = sheet.cell(row_number, 9, str(record.get('in_record') or ''))
            cls._fit_record_id(record_cell)
            unit_price = record.get('unit_price')
            if unit_price in (None, ''):
                unit_price = 0
            price_cell = sheet.cell(row_number, 10, unit_price)
            price_cell.number_format = '#,##0.00'
            amount_cell = sheet.cell(row_number, 11)
            if unit_price not in (None, '') and record.get('quantity') not in (None, ''):
                try:
                    amount = Decimal(str(unit_price)) * Decimal(str(record['quantity']))
                except (InvalidOperation, TypeError, ValueError):
                    amount = None
                if amount is not None:
                    amount_cell.value = float(amount)
            amount_cell.number_format = '#,##0.00'
            for column_number in detail_columns:
                detail_alignment = copy(sheet.cell(row_number, column_number).alignment)
                detail_alignment.horizontal = 'left'
                detail_alignment.vertical = 'center'
                detail_alignment.indent = 0
                detail_alignment.wrap_text = False
                sheet.cell(row_number, column_number).alignment = detail_alignment

        last_detail_row = max(12, 6 + len(records))
        sheet.cell(total_row, 7, f'=SUM(G7:G{last_detail_row})')
        sheet.cell(total_row, 7).number_format = '0'
        sheet.cell(total_row, 11, f'=SUM(K7:K{last_detail_row})')
        sheet.cell(total_row, 11).number_format = '#,##0.00'
        for column_number in detail_columns:
            total_alignment = copy(sheet.cell(total_row, column_number).alignment)
            total_alignment.horizontal = 'left'
            total_alignment.vertical = 'center'
            total_alignment.indent = 0
            total_alignment.wrap_text = False
            sheet.cell(total_row, column_number).alignment = total_alignment
        cls._bold_labels(sheet, (
            'A2', 'E2', 'A3', 'E3', 'A4', 'E4', 'A5',
            'A6', 'C6', 'E6', 'G6', 'H6', 'I6', 'J6', 'K6',
        ))
        sheet.print_area = f'A1:K{signature_row}'
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0

        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return f'批量入库单_{datetime.now():%Y%m%d%H%M%S}.xlsx', stream

    @classmethod
    def export_outbound(cls, records):
        workbook = load_workbook(cls.TEMPLATE_DIR / 'outbound_template.xlsx')
        sheet = workbook.active
        sheet.title = '出库单'
        cls._add_outbound_date_column(sheet)
        total_row, signature_row = cls._expand_detail_rows(sheet, 11, 12, 13, len(records))

        sheet['A2'] = '制单日期'
        sheet['B2'] = datetime.now().date()
        sheet['B2'].number_format = 'yyyy-mm-dd'
        sheet['F2'] = cls._common_value(records, 'shelf_location', '多货架')
        shelf_alignment = copy(sheet['F2'].alignment)
        shelf_alignment.horizontal = 'left'
        sheet['F2'].alignment = shelf_alignment
        sheet['I3'] = None
        sheet['J3'] = None
        sheet['K3'] = '出库类别'
        sheet['L3'] = '研发领用'
        sheet['B4'] = ''
        sheet.cell(signature_row, 2, '')

        sheet['H5'] = '单价'
        sheet['I5'] = '总价'
        sheet['J5'] = '出库日期'
        sheet['K5'] = '出库记录号'
        sheet['L5'] = '货架'
        detail_columns = (1, 3, 5, 7, 8, 9, 10, 11, 12)
        for column_number in detail_columns:
            header_alignment = copy(sheet.cell(5, column_number).alignment)
            header_alignment.horizontal = 'center'
            header_alignment.vertical = 'center'
            header_alignment.indent = 0
            sheet.cell(5, column_number).alignment = header_alignment

        for row_number, record in enumerate(records, start=6):
            sheet.cell(row_number, 1, record.get('display_goods_id') or record.get('goods_id') or '')
            sheet.cell(row_number, 3, record.get('goods_name') or '')
            model_cell = sheet.cell(row_number, 5, cls._model_text(record))
            model_cell.number_format = '@'
            sheet.cell(row_number, 7, record.get('quantity'))
            sheet.cell(row_number, 7).number_format = '0'
            unit_price = record.get('unit_price')
            if unit_price in (None, ''):
                unit_price = 0
            price_cell = sheet.cell(row_number, 8, unit_price)
            price_cell.number_format = '#,##0.00'
            amount_cell = sheet.cell(row_number, 9)
            if record.get('quantity') not in (None, ''):
                try:
                    amount = Decimal(str(unit_price)) * Decimal(str(record['quantity']))
                except (InvalidOperation, TypeError, ValueError):
                    amount = None
                if amount is not None:
                    amount_cell.value = float(amount)
            amount_cell.number_format = '#,##0.00'
            date_cell = sheet.cell(row_number, 10, record.get('out_date') or '')
            date_cell.number_format = 'yyyy-mm-dd'
            record_cell = sheet.cell(row_number, 11, str(record.get('out_record_id') or ''))
            cls._fit_record_id(record_cell)
            sheet.cell(row_number, 12, record.get('shelf_location') or '')
            for column_number in detail_columns:
                detail_alignment = copy(sheet.cell(row_number, column_number).alignment)
                detail_alignment.horizontal = 'left'
                detail_alignment.vertical = 'center'
                detail_alignment.indent = 0
                detail_alignment.wrap_text = False
                sheet.cell(row_number, column_number).alignment = detail_alignment

        last_detail_row = max(11, 5 + len(records))
        sheet.cell(total_row, 7, f'=SUM(G6:G{last_detail_row})')
        sheet.cell(total_row, 7).number_format = '0'
        sheet.cell(total_row, 9, f'=SUM(I6:I{last_detail_row})')
        sheet.cell(total_row, 9).number_format = '#,##0.00'
        sheet.cell(total_row, 12).value = None
        for column_number in detail_columns:
            total_alignment = copy(sheet.cell(total_row, column_number).alignment)
            total_alignment.horizontal = 'left'
            total_alignment.vertical = 'center'
            total_alignment.indent = 0
            total_alignment.wrap_text = False
            sheet.cell(total_row, column_number).alignment = total_alignment
        cls._bold_labels(sheet, (
            'A2', 'E2', 'A3', 'E3', 'K3', 'A4',
            'A5', 'C5', 'E5', 'G5', 'H5', 'I5', 'J5', 'K5', 'L5',
        ))
        sheet.print_area = f'A1:L{signature_row}'
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0

        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return f'批量出库单_{datetime.now():%Y%m%d%H%M%S}.xlsx', stream
