import type { Role } from "./lib/navigation";

export interface User {
  id: string;
  username: string;
  displayName: string;
  role: Role;
  organizationId: string | null;
  organizationName: string | null;
  identityLabel?: string | null;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  csrfToken: string;
  user: User;
}

export interface PatientDashboardData {
  patient: {
    id: string;
    displayName: string;
    recordNumber: string;
    regionCode: string;
  };
  plan: {
    id: string;
    title: string;
    status: string;
    version: number;
    startDate: string;
    endDate: string | null;
    content: {
      summary?: string;
      phases?: Array<{ name: string; durationDays: number }>;
    };
  } | null;
  tasks: Array<{
    id: string;
    title: string;
    description: string;
    category: string;
    dueAt: string;
    status: string;
    isOverdue: boolean;
  }>;
  medications: Array<{
    id: string;
    drugName: string;
    doseText: string;
    frequencyText: string;
    status: string;
  }>;
  alerts: Array<{
    id: string;
    title: string;
    detail: string;
    severity: string;
    status: string;
    createdAt: string;
  }>;
  caregivers: Array<{
    caregiverUserId: string;
    displayName: string;
    scopes: string[];
    active: boolean;
    expiresAt: string | null;
  }>;
}

export interface DoctorDashboardData {
  activePlans: number;
  patientCount: number;
  openAlerts: number;
  taskCompletionRate: number;
  patients: Array<{
    patient: {
      id: string;
      displayName: string;
      recordNumber: string;
    };
    planId: string;
    planStatus: string;
    openTasks: number;
    openAlerts: number;
  }>;
}

export interface HospitalDashboardData {
  organization: {
    name: string;
    type: string;
    regionCode: string;
    verified: boolean;
  };
  activePlans: number;
  doctorCount: number;
  taskCompletionRate: number;
  openAlerts: number;
  recentAlerts: PatientDashboardData["alerts"];
}

export interface GovernmentMetricsData {
  generatedAt: string;
  minimumCellSize: number;
  regions: Array<{
    regionCode: string;
    activePlans: number | null;
    taskCompletionRate: number | null;
    openAlerts: number | null;
    suppressed: boolean;
  }>;
  disclaimers: string[];
}

export interface ReviewCase {
  id: string;
  organizationId: string;
  type: string;
  subject: string;
  status: string;
  decisionNote: string | null;
  createdAt: string;
}

export interface PharmaDashboardData {
  products: Array<{
    id: string;
    name: string;
    approvalNumber: string;
    manufacturer: string;
    verificationStatus: string;
    status: string;
  }>;
  demandSignals: Array<{
    regionCode: string;
    drugName: string;
    period: string;
    organizationCount: number;
    patientMonths: number;
    published: boolean;
  }>;
  capacityReports: Array<{
    id: string;
    productId: string;
    regionCode: string;
    period: string;
    capacityUnits: number;
    status: string;
    createdAt: string;
  }>;
  disclaimers: string[];
}

export interface OfficialDataset {
  id: string;
  sourceCode: string;
  title: string;
  version: string;
  sourceUrl: string;
  publishedAt: string | null;
  effectiveAt: string | null;
  importedAt: string;
  checksum: string;
  parserVersion: string;
  reviewer: string;
  status: string;
}
