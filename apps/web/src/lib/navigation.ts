export type Role =
  | "PATIENT"
  | "CAREGIVER"
  | "DOCTOR"
  | "HOSPITAL_ADMIN"
  | "REGULATOR"
  | "PHARMA"
  | "COMMUNITY_ORG"
  | "SYSTEM_ADMIN";

export type SectionKey =
  | "patient"
  | "doctor"
  | "hospital"
  | "government"
  | "pharma"
  | "community"
  | "admin";

const roleLabels: Record<Role, string> = {
  PATIENT: "用户 · 病患",
  CAREGIVER: "用户 · 家属",
  DOCTOR: "医院 · 医生",
  HOSPITAL_ADMIN: "医院 · 管理",
  REGULATOR: "政府 · 入驻认证",
  PHARMA: "药企",
  COMMUNITY_ORG: "社区与志愿组织",
  SYSTEM_ADMIN: "系统管理",
};

const roleSections: Record<Role, SectionKey> = {
  PATIENT: "patient",
  CAREGIVER: "patient",
  DOCTOR: "doctor",
  HOSPITAL_ADMIN: "hospital",
  REGULATOR: "government",
  PHARMA: "pharma",
  COMMUNITY_ORG: "community",
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
  government: "区域监管与入驻认证",
  pharma: "药品供应与产能",
  community: "社区照护与志愿调度",
  admin: "官方数据管理",
};
