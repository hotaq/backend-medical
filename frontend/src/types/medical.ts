// Medical Triage-BOTS Frontend Types
// TypeScript definitions for medical triage data structures

export interface PatientInfo {
  patient_id?: string;
  age?: number;
  gender?: string;
  medical_record_number?: string;
}

export interface StructuredData {
  data_type: StructuredDataType;
  data: Record<string, any>;
  units?: Record<string, string>;
  reference_ranges?: Record<string, { min: number; max: number }>;
  test_date?: string;
}

export interface ImageData {
  image_path: string;
  image_type?: string;
  uploaded_at?: string;
  file_size?: number;
}

export interface TriageCase {
  case_id?: string;
  created_at?: string;
  priority_level?: UrgencyLevel;
  patient_info?: PatientInfo;
  symptoms_text?: string;
  chief_complaint?: string;
  medical_history?: string;
  additional_notes?: string;
  structured_data?: StructuredData[];
  images?: ImageData[];
  primary_data_type?: DataType;
  requires_vision_analysis?: boolean;
  requires_text_analysis?: boolean;
  requires_structured_analysis?: boolean;
  target_department?: string;
  specialty_required?: string;
}

export interface TriageCaseResponse {
  case_id: string;
  processing_status: string;
  triage_score?: number;
  urgency_level?: UrgencyLevel;
  estimated_wait_time?: number;
  recommendations?: string[];
  processed_at: string;
  vision_analysis_completed: boolean;
  text_analysis_completed: boolean;
  structured_analysis_completed: boolean;
  raw_vision_output?: any;
  synthesized_vision_output?: string;
  raw_text_output?: any;
  synthesized_text_output?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  case_id?: string;
  metadata?: {
    processing_time?: number;
    model_used?: string;
    confidence?: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  components: {
    chief_bot: string;
    database: string;
    vision_bot: string;
    text_bot: string;
  };
}

export interface SystemMetrics {
  metrics: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    average_processing_time: number;
    critical_cases: number;
    high_priority_cases: number;
    text_only_cases: number;
    image_cases: number;
    multimodal_cases: number;
  };
  timestamp: string;
}

export interface DatabaseCase {
  id: number;
  case_id: string;
  patient_id?: number;
  symptoms_text?: string;
  chief_complaint?: string;
  medical_history?: string;
  additional_notes?: string;
  primary_data_type?: DataType;
  priority_level?: UrgencyLevel;
  target_department?: string;
  specialty_required?: string;
  requires_vision_analysis: boolean;
  requires_text_analysis: boolean;
  requires_structured_analysis: boolean;
  created_at: string;
  updated_at?: string;
  patient?: DatabasePatient;
  structured_data?: DatabaseStructuredData[];
  images?: DatabaseImage[];
  triage_result?: DatabaseTriageResult;
}

export interface DatabasePatient {
  id: number;
  patient_id: string;
  age?: number;
  gender?: string;
  medical_record_number?: string;
  created_at: string;
  updated_at?: string;
}

export interface DatabaseStructuredData {
  id: number;
  triage_case_id: number;
  data_type: StructuredDataType;
  data: Record<string, any>;
  units?: Record<string, string>;
  reference_ranges?: Record<string, any>;
  test_date?: string;
  created_at: string;
}

export interface DatabaseImage {
  id: number;
  triage_case_id: number;
  image_path: string;
  image_type?: string;
  file_size?: number;
  processed: boolean;
  processing_error?: string;
  uploaded_at: string;
}

export interface DatabaseTriageResult {
  id: number;
  triage_case_id: number;
  final_triage_score: number;
  urgency_level: UrgencyLevel;
  estimated_wait_time?: number;
  recommendations?: string[];
  clinical_notes?: string;
  vision_analysis_completed: boolean;
  text_analysis_completed: boolean;
  structured_analysis_completed: boolean;
  scoring_algorithm_version?: string;
  feature_weights?: Record<string, any>;
  confidence_score?: number;
  review_required: boolean;
  reviewed_by?: string;
  review_notes?: string;
  processed_at: string;
  reviewed_at?: string;
}

export interface ProcessingRecord {
  id: number;
  triage_case_id: number;
  agent_type: string;
  processing_step: string;
  status: ProcessingStatus;
  raw_output?: any;
  confidence_score?: number;
  model_version?: string;
  synthesized_output?: string;
  llm_model_used?: string;
  processing_time_ms?: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface VitalSigns {
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  heart_rate?: number;
  temperature?: number;
  respiratory_rate?: number;
  oxygen_saturation?: number;
  glasgow_coma_scale?: number;
}

export interface BloodTest {
  fasting_glucose?: number;
  hba1c?: number;
  total_cholesterol?: number;
  ldl_cholesterol?: number;
  hdl_cholesterol?: number;
  triglycerides?: number;
  white_blood_count?: number;
  red_blood_count?: number;
  hemoglobin?: number;
  hematocrit?: number;
  platelet_count?: number;
}

export interface LabResults {
  sodium?: number;
  potassium?: number;
  chloride?: number;
  co2?: number;
  bun?: number;
  creatinine?: number;
  egfr?: number;
  albumin?: number;
  total_protein?: number;
  alkaline_phosphatase?: number;
  alt?: number;
  ast?: number;
  total_bilirubin?: number;
}

// Enums
export enum DataType {
  TEXT = 'text',
  STRUCTURED = 'structured',
  IMAGE = 'image',
  MIXED = 'mixed'
}

export enum UrgencyLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum StructuredDataType {
  BLOOD_TEST = 'blood_test',
  VITAL_SIGNS = 'vital_signs',
  MEDICAL_HISTORY = 'medical_history',
  LAB_RESULTS = 'lab_results',
  OTHER = 'other'
}

export enum ProcessingStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum ImageType {
  RETINAL = 'retinal',
  XRAY = 'xray',
  CT_SCAN = 'ct_scan',
  MRI = 'mri',
  ULTRASOUND = 'ultrasound',
  GENERAL = 'general'
}

// Utility types
export type UrgencyColor = 'green' | 'yellow' | 'orange' | 'red';
export type ProcessingStatusColor = 'gray' | 'blue' | 'green' | 'red';

// API Response types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Form types
export interface TriageCaseForm {
  patient_info: {
    patient_id: string;
    age: string;
    gender: string;
    medical_record_number: string;
  };
  symptoms_text: string;
  chief_complaint: string;
  medical_history: string;
  additional_notes: string;
  structured_data: StructuredDataForm[];
  images: File[];
  target_department: string;
  specialty_required: string;
}

export interface StructuredDataForm {
  data_type: StructuredDataType;
  fields: { key: string; value: string; unit?: string }[];
  test_date: string;
}

export interface ChatForm {
  message: string;
  case_id?: string;
  include_context: boolean;
}

// Chart data types
export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface UrgencyDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface ProcessingMetrics {
  total_cases: number;
  avg_processing_time: number;
  success_rate: number;
  error_rate: number;
  cases_by_hour: TimeSeriesDataPoint[];
  urgency_distribution: UrgencyDistribution;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'case_update' | 'system_status' | 'metrics_update' | 'error';
  payload: any;
  timestamp: string;
}

export interface CaseUpdateMessage {
  case_id: string;
  status: ProcessingStatus;
  progress?: number;
  agent?: string;
  step?: string;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// UI State types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface FilterState {
  urgency_levels: UrgencyLevel[];
  date_range: {
    start: string;
    end: string;
  };
  departments: string[];
  search_query: string;
  processing_status: ProcessingStatus[];
}

export interface SortState {
  field: string;
  direction: 'asc' | 'desc';
}

// Constants
export const URGENCY_COLORS: Record<UrgencyLevel, UrgencyColor> = {
  [UrgencyLevel.LOW]: 'green',
  [UrgencyLevel.MEDIUM]: 'yellow',
  [UrgencyLevel.HIGH]: 'orange',
  [UrgencyLevel.CRITICAL]: 'red'
};

export const PROCESSING_STATUS_COLORS: Record<ProcessingStatus, ProcessingStatusColor> = {
  [ProcessingStatus.PENDING]: 'gray',
  [ProcessingStatus.IN_PROGRESS]: 'blue',
  [ProcessingStatus.COMPLETED]: 'green',
  [ProcessingStatus.FAILED]: 'red',
  [ProcessingStatus.CANCELLED]: 'gray'
};

export const URGENCY_LABELS: Record<UrgencyLevel, string> = {
  [UrgencyLevel.LOW]: 'Low Priority',
  [UrgencyLevel.MEDIUM]: 'Medium Priority',
  [UrgencyLevel.HIGH]: 'High Priority',
  [UrgencyLevel.CRITICAL]: 'Critical'
};

export const DATA_TYPE_LABELS: Record<DataType, string> = {
  [DataType.TEXT]: 'Text Only',
  [DataType.STRUCTURED]: 'Structured Data',
  [DataType.IMAGE]: 'Images',
  [DataType.MIXED]: 'Multi-modal'
};
