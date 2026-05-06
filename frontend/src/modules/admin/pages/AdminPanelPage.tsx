import BackupsPanel from "../components/BackupsPanel";
import TaskHistoryViewer from "../components/TaskHistoryViewer";
import TaskTypesPanel from "../components/TaskTypesPanel";

export default function AdminPanelPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Panel administracyjny</h1>
        <p className="mt-1 text-sm text-gray-600">
          Zarządzanie słownikami systemu, kopiami zapasowymi bazy i dziennikiem zmian zadań.
        </p>
      </header>

      <TaskTypesPanel />
      <BackupsPanel />
      <TaskHistoryViewer />
    </div>
  );
}
