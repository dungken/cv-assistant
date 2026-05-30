export const ROLES = [
    { id: 'backend', label: 'Backend' },
    { id: 'frontend', label: 'Frontend' },
    { id: 'fullstack', label: 'Fullstack' },
    { id: 'mobile', label: 'Mobile' },
    { id: 'data', label: 'Data' },
    { id: 'ai_engineer', label: 'AI/ML' },
    { id: 'devops', label: 'DevOps' },
    { id: 'cloud', label: 'Cloud' },
    { id: 'security', label: 'Security' },
    { id: 'qa', label: 'QA/Tester' },
    { id: 'ba', label: 'Business Analyst' },
    { id: 'pm', label: 'Product Manager' },
    { id: 'design', label: 'UI/UX Design' },
];

export const SENIORITIES = [
    { id: 'fresher', label: 'Fresher' },
    { id: 'junior', label: 'Junior' },
    { id: 'mid', label: 'Mid' },
    { id: 'senior', label: 'Senior' },
    { id: 'lead', label: 'Lead' },
    { id: 'manager', label: 'Manager' },
];

export const LOCATIONS = [
    { id: 'HCM', label: 'HCM' },
    { id: 'HN', label: 'Hà Nội' },
    { id: 'DN', label: 'Đà Nẵng' },
    { id: 'Remote', label: 'Remote' },
    { id: 'Any', label: 'Bất kỳ' },
];

export const WORK_MODES = [
    { id: 'onsite', label: 'Onsite' },
    { id: 'hybrid', label: 'Hybrid' },
    { id: 'remote', label: 'Remote' },
];

export const SENIORITY_EXP_MAPPING: Record<string, { default: number; min: number; max: number }> = {
    fresher: { default: 0, min: 0, max: 1 },
    junior:  { default: 1, min: 0, max: 3 },
    mid:     { default: 3, min: 2, max: 5 },
    senior:  { default: 5, min: 4, max: 8 },
    lead:    { default: 7, min: 5, max: 15 },
    manager: { default: 8, min: 6, max: 20 },
};
