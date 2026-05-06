export interface TaskType {
  taskTypeId: number;
  name: string;
  createdAt: string;
}

export interface BackupResponse {
  backupId: number;
  timestamp: string;
  status: string;
}

export interface ActivityLogEntry {
  activityLogId: number;
  taskId: number;
  userId: number;
  action: string;
  fieldName: string | null;
  oldValue: string | null;
  newValue: string | null;
  createdAt: string;
}
