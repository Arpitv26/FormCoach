/* Generated from contracts/api.schema.json. Do not edit by hand. Run npm run contracts:generate. */

/**
 * Schema bundle for generating matching frontend types; not an API endpoint.
 */
export interface ApiContract {
  analysisResponse: AnalysisResponse;
  videoAnalysisResponse: VideoAnalysisResponse;
  liveBatchRequest: LiveBatchRequest;
  coachRequest: CoachRequest;
  coachResponse: CoachResponse;
  healthResponse: HealthResponse;
  errorResponse: ErrorResponse;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "AnalysisResponse".
 */
export interface AnalysisResponse {
  contractVersion: "1.0";
  sessionId: string;
  status: "complete" | "partial" | "insufficient_data" | "not_implemented";
  provenance: Provenance;
  source: Source;
  exercise: Exercise | null;
  cameraQuality: CameraQuality;
  summary: Summary;
  metrics: SessionMetrics;
  reps: RepAnalysis[];
  issues: Issue[];
  timeline: TimelineEvent[];
  limitations: string[];
  scoring: ScoringInfo | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Provenance".
 */
export interface Provenance {
  kind: "measured" | "synthetic" | "placeholder";
  label: string;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Source".
 */
export interface Source {
  type: "live" | "upload";
  durationMs: number | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Exercise".
 */
export interface Exercise {
  id: string;
  name: string;
  confidence: number | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "CameraQuality".
 */
export interface CameraQuality {
  score: number | null;
  fullBodyVisible: boolean | null;
  issues: string[];
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Summary".
 */
export interface Summary {
  overallScore: number | null;
  totalReps: number | null;
  primaryFocus: string | null;
  headline: string;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "SessionMetrics".
 */
export interface SessionMetrics {
  rangeOfMotion: number | null;
  symmetry: number | null;
  tempo: number | null;
  stability: number | null;
  consistency: number | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "RepAnalysis".
 */
export interface RepAnalysis {
  repNumber: number;
  startMs: number;
  endMs: number;
  score: number | null;
  metrics: RepMetrics;
  measurements: {
    [k: string]: number | null;
  };
  issues: Issue[];
  keyMoments: KeyMoment[];
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "RepMetrics".
 */
export interface RepMetrics {
  rangeOfMotion: number | null;
  symmetry: number | null;
  tempo: number | null;
  stability: number | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "Issue".
 */
export interface Issue {
  id: string;
  code: string;
  severity: "low" | "medium" | "high";
  confidence: number | null;
  title: string;
  shortCue: string;
  explanation: string;
  startMs: number;
  endMs: number;
  involvedJoints: string[];
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "KeyMoment".
 */
export interface KeyMoment {
  timestampMs: number;
  type: string;
  label: string;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "TimelineEvent".
 */
export interface TimelineEvent {
  timestampMs: number;
  type: "rep_start" | "rep_end" | "key_moment" | "issue";
  repNumber: number | null;
  issueId: string | null;
  label: string;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ScoringInfo".
 */
export interface ScoringInfo {
  version: string;
  method: string;
  weights: {
    [k: string]: number;
  };
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "VideoAnalysisResponse".
 */
export interface VideoAnalysisResponse {
  contractVersion?: "1.0";
  analysis: AnalysisResponse;
  poseTrack: PoseTrack;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "PoseTrack".
 */
export interface PoseTrack {
  imageWidth: number;
  imageHeight: number;
  durationMs: number;
  /**
   * @maxItems 1800
   */
  frames: PoseFrame[];
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "PoseFrame".
 */
export interface PoseFrame {
  frameIndex: number;
  timestampMs: number;
  /**
   * @maxItems 33
   */
  landmarks: PoseLandmark[];
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "PoseLandmark".
 */
export interface PoseLandmark {
  index: number;
  name: string;
  x: number;
  y: number;
  z?: number | null;
  visibility?: number | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "LiveBatchRequest".
 */
export interface LiveBatchRequest {
  contractVersion?: "1.0";
  sessionId: string;
  exerciseHint?: string | null;
  /**
   * @maxItems 1800
   */
  frames: PoseFrame[];
  isFinal?: boolean;
  imageWidth: number;
  imageHeight: number;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "CoachRequest".
 */
export interface CoachRequest {
  analysis: AnalysisResponse;
  mode: "summary" | "next_set" | "qa";
  question?: string | null;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "CoachResponse".
 */
export interface CoachResponse {
  contractVersion: "1.0";
  sessionId: string;
  mode: "summary" | "next_set" | "qa";
  provider: "fallback" | "openai";
  message: string;
  evidence: string[];
  limitations: string[];
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "HealthResponse".
 */
export interface HealthResponse {
  status: "ok";
  service: "formcoach-api";
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ErrorResponse".
 */
export interface ErrorResponse {
  detail: ErrorDetail;
}
/**
 * This interface was referenced by `ApiContract`'s JSON-Schema
 * via the `definition` "ErrorDetail".
 */
export interface ErrorDetail {
  code: string;
  message: string;
}
