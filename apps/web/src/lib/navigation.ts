export type Role =
  | "PATIENT"
  | "CAREGIVER"
  | "DOCTOR"
  | "HOSPITAL_ADMIN"
  | "REGULATOR"
  | "PHARMA"
  | "SYSTEM_ADMIN";

export type SectionKey =
  | "patient"
  | "doctor"
  | "hospital"
  | "government"
  | "pharma"
  | "admin";

const roleLabels: Record<Role, string> = {
  PATIENT: "患者",
  CAREGIVER: "家属",
  DOCTOR: "医生",
  HOSPITAL_ADMIN: "医院",
  REGULATOR: "政府",
  PHARMA: "药企",
  SYSTEM_ADMIN: "系统管理",
};

const roleSections: Record<Role, SectionKey> = {
  PATIENT: "patient",
  CAREGIVER: "patient",
  DOCTOR: "doctor",
  HOSPITAL_ADMIN: "hospital",
  REGULATOR: "government",
  PHARMA: "pharma",
  SYSTEM_ADMIN: "admin",
};

export function roleLabel(role: Role): string {
  return roleLabels[role];
}

export function defaultSectionForRole(role: Role): SectionKey {
  return roleSections[role];
}

export const sectionLabels: Record<SectionKey, string> = {
  patient: "我的治疗进度",
  doctor: "医生工作台",
  hospital: "医院协同中心",
  government: "区域监管沙箱",
  pharma: "药品需求与产能",
  admin: "官方数据管理",
};
