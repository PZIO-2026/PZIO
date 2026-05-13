import { useEffect, useRef, useState } from "react";

import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Modal from "../Modal";

import type {
  BurndownData,
  Sprint,
} from "../../types";

interface Props {
  isOpen: boolean;

  onClose: () => void;

  sprint: Sprint | null;

  burndown: BurndownData | null;

  isLoading: boolean;
}

function BurndownChart({
  burndown,
}: {
  burndown: BurndownData;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [chartSize, setChartSize] = useState({
    width: 0,
    height: 0,
  });

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) return;

    let frameId = 0;

    function updateSize() {
      const rect = container?.getBoundingClientRect();
      const width = Math.floor(rect?.width || 0);
      const height = Math.floor(rect?.height || 0);

      if (width <= 0 || height <= 0) return;

      setChartSize((current) =>
        current.width === width && current.height === height
          ? current
          : { width, height },
      );
    }

    const resizeObserver = new ResizeObserver(() => {
      cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(updateSize);
    });

    resizeObserver.observe(container);
    frameId = requestAnimationFrame(updateSize);

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
    };
  }, []);

  const chartData = burndown.days.map((day) => ({
    date: new Date(day.date).toLocaleDateString("pl-PL"),
    remainingPoints: day.remainingPoints,
  }));

  return (
    <div ref={containerRef} className="h-100 min-w-0 w-full">
      {chartSize.width > 0 && chartSize.height > 0 && (
        <LineChart
          width={chartSize.width}
          height={chartSize.height}
          data={chartData}
        >
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="date" />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="remainingPoints"
            strokeWidth={3}
          />
        </LineChart>
      )}
    </div>
  );
}

export default function SprintBurndownModal({
  isOpen,
  onClose,
  sprint,
  burndown,
  isLoading,
}: Props) {
  return (
    <Modal
      title={
        sprint
          ? `Burndown — ${sprint.name}`
          : "Burndown"
      }
      isOpen={isOpen}
      onClose={onClose}
    >
      {isLoading ? (
        <div className="py-10 text-center text-sm text-gray-500">
          Ładowanie wykresu...
        </div>
      ) : burndown === null ? (
        <div className="py-10 text-center text-sm text-gray-500">
          Brak danych burndown.
        </div>
      ) : (
        <>
          {/* Stats */}

          <div className="mb-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">
                Sprint ID
              </p>

              <p className="mt-2 text-2xl font-bold text-gray-900">
                {burndown.sprintId}
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">
                Total points
              </p>

              <p className="mt-2 text-2xl font-bold text-gray-900">
                {burndown.totalPoints}
              </p>
            </div>
          </div>

          {/* Chart */}

          <BurndownChart burndown={burndown} />
        </>
      )}
    </Modal>
  );
}