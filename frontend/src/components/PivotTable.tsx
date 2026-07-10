import { useEffect, useRef } from 'react';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import 'tabulator-tables/dist/css/tabulator_simple.min.css';

type Props = {
  data: Record<string, unknown>[];
  onCellEdit?: (id: number, field: string, value: number) => void;
};

export default function PivotTable({ data, onCellEdit }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const tableRef = useRef<Tabulator | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    tableRef.current?.destroy();
    tableRef.current = new Tabulator(ref.current, {
      data,
      layout: 'fitDataStretch',
      height: '480px',
      reactiveData: true,
      columns: [
        { title: 'Объект', field: 'object_code', width: 110 },
        { title: 'Форма', field: 'form_code', width: 90 },
        { title: 'Статья', field: 'line_item', minWidth: 160 },
        { title: 'Период', field: 'period', width: 100 },
        {
          title: 'База',
          field: 'base_amount',
          editor: 'number',
          hozAlign: 'right',
          formatter: 'money',
          formatterParams: { symbol: '', precision: 0 },
        },
        {
          title: 'Корректировка',
          field: 'adjustment',
          editor: 'number',
          hozAlign: 'right',
          formatter: 'money',
          formatterParams: { symbol: '', precision: 0 },
        },
        {
          title: 'Итого',
          field: 'consensus_amount',
          hozAlign: 'right',
          formatter: 'money',
          formatterParams: { symbol: '', precision: 0 },
        },
        {
          title: 'Факт',
          field: 'actual_amount',
          hozAlign: 'right',
          formatter: 'money',
          formatterParams: { symbol: '', precision: 0 },
        },
      ],
    });

    tableRef.current.on('cellEdited', (cell) => {
      const row = cell.getRow().getData() as { id: number };
      const field = cell.getField();
      const value = Number(cell.getValue());
      if (onCellEdit && (field === 'base_amount' || field === 'adjustment')) {
        onCellEdit(row.id, field, value);
      }
    });

    return () => {
      tableRef.current?.destroy();
      tableRef.current = null;
    };
  }, [data, onCellEdit]);

  return <div className="tabulator-host" ref={ref} />;
}
