import { useEffect, useRef } from 'react';
import { TabulatorFull as Tabulator } from 'tabulator-tables';

interface Props {
  data: Record<string, unknown>[];
  editable?: boolean;
  onCellEdit?: (id: string, field: string, value: number) => void;
}

export default function PivotTable({ data, editable, onCellEdit }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const tableRef = useRef<Tabulator | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (tableRef.current) tableRef.current.destroy();

    tableRef.current = new Tabulator(ref.current, {
      data,
      layout: 'fitDataStretch',
      groupBy: ['construction_object_name', 'form_code'],
      columns: [
        { title: 'Статья', field: 'line_item', width: 150 },
        { title: 'Период', field: 'period', width: 100 },
        { title: 'База', field: 'base_amount', editor: editable ? 'number' : undefined, formatter: 'money', formatterParams: { precision: 2 } },
        { title: 'Корректировка', field: 'adjustment', editor: editable ? 'number' : undefined, formatter: 'money', formatterParams: { precision: 2 } },
        { title: 'Итого', field: 'consensus_amount', formatter: 'money', formatterParams: { precision: 2 } },
        { title: 'Факт', field: 'actual_amount', formatter: 'money', formatterParams: { precision: 2 } },
      ],
      cellEdited: (cell) => {
        const row = cell.getRow().getData() as Record<string, unknown>;
        onCellEdit?.(row.id as string, cell.getField(), cell.getValue() as number);
        cell.getElement().setAttribute('data-modified', 'true');
      },
    });

    return () => { tableRef.current?.destroy(); };
  }, [data, editable, onCellEdit]);

  return <div ref={ref} />;
}
