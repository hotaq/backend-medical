"use client";

import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useForm, useFieldArray } from "react-hook-form";
import { useDropzone } from "react-dropzone";
import {
  PlusIcon,
  XMarkIcon,
  PhotoIcon,
  DocumentTextIcon,
  ChartBarIcon,
  UserIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import { useMutation } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import apiService from "../services/api";
import {
  TriageCase,
  TriageCaseResponse,
  StructuredDataType,
  ImageType,
  UrgencyLevel,
  DataType,
} from "../types/medical";
import Layout from "../components/Layout";

interface TriageCaseFormData {
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
  structured_data: Array<{
    data_type: StructuredDataType;
    fields: Array<{ key: string; value: string; unit: string }>;
    test_date: string;
  }>;
  target_department: string;
  specialty_required: string;
}

export default function TriagePage() {
  const [uploadedImages, setUploadedImages] = useState<File[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [triageResult, setTriageResult] = useState<TriageCaseResponse | null>(
    null,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<TriageCaseFormData>({
    defaultValues: {
      patient_info: {
        patient_id: "",
        age: "",
        gender: "",
        medical_record_number: "",
      },
      symptoms_text: "",
      chief_complaint: "",
      medical_history: "",
      additional_notes: "",
      structured_data: [],
      target_department: "",
      specialty_required: "",
    },
  });

  const {
    fields: structuredDataFields,
    append: appendStructuredData,
    remove: removeStructuredData,
  } = useFieldArray({
    control,
    name: "structured_data",
  });

  // File upload handling
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setUploadedImages((prev) => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpeg", ".jpg", ".png", ".bmp", ".tiff"],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeImage = (index: number) => {
    setUploadedImages((prev) => prev.filter((_, i) => i !== index));
  };

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async (data: TriageCaseFormData) => {
      setIsSubmitting(true);

      // Convert form data to TriageCase
      const triageCase: TriageCase = {
        patient_info: {
          patient_id: data.patient_info.patient_id || undefined,
          age: data.patient_info.age
            ? parseInt(data.patient_info.age)
            : undefined,
          gender: data.patient_info.gender || undefined,
          medical_record_number:
            data.patient_info.medical_record_number || undefined,
        },
        symptoms_text: data.symptoms_text || undefined,
        chief_complaint: data.chief_complaint || undefined,
        medical_history: data.medical_history || undefined,
        additional_notes: data.additional_notes || undefined,
        structured_data: data.structured_data.map((sd) => ({
          data_type: sd.data_type,
          data: sd.fields.reduce(
            (acc, field) => {
              if (field.key && field.value) {
                acc[field.key] = isNaN(Number(field.value))
                  ? field.value
                  : Number(field.value);
              }
              return acc;
            },
            {} as Record<string, any>,
          ),
          units: sd.fields.reduce(
            (acc, field) => {
              if (field.key && field.unit) {
                acc[field.key] = field.unit;
              }
              return acc;
            },
            {} as Record<string, string>,
          ),
          test_date: sd.test_date || undefined,
        })),
        images: uploadedImages.map((file, index) => ({
          image_path: `/uploads/${Date.now()}_${index}_${file.name}`,
          image_type: detectImageType(file.name),
          file_size: file.size,
        })),
        target_department: data.target_department || undefined,
        specialty_required: data.specialty_required || undefined,
      };

      // Use multipart if we have images
      if (uploadedImages.length > 0) {
        const formData = new FormData();

        // Add form fields
        if (triageCase.symptoms_text)
          formData.append("symptoms_text", triageCase.symptoms_text);
        if (triageCase.chief_complaint)
          formData.append("chief_complaint", triageCase.chief_complaint);
        if (triageCase.medical_history)
          formData.append("medical_history", triageCase.medical_history);
        if (triageCase.patient_info?.patient_id)
          formData.append("patient_id", triageCase.patient_info.patient_id);
        if (triageCase.patient_info?.age)
          formData.append("age", triageCase.patient_info.age.toString());
        if (triageCase.patient_info?.gender)
          formData.append("gender", triageCase.patient_info.gender);
        if (triageCase.structured_data)
          formData.append(
            "structured_data",
            JSON.stringify(triageCase.structured_data),
          );

        // Add images
        uploadedImages.forEach((file, index) => {
          formData.append("images", file);
        });

        return apiService.submitTriageCaseMultipart(formData);
      } else {
        return apiService.submitTriageCase(triageCase);
      }
    },
    onSuccess: (result) => {
      setTriageResult(result);
      setCurrentStep(4); // Move to results step
      toast.success("Triage case submitted successfully!");
    },
    onError: (error) => {
      console.error("Submission error:", error);
      toast.error("Failed to submit triage case. Please try again.");
    },
    onSettled: () => {
      setIsSubmitting(false);
    },
  });

  const onSubmit = (data: TriageCaseFormData) => {
    submitMutation.mutate(data);
  };

  const addStructuredData = () => {
    appendStructuredData({
      data_type: StructuredDataType.VITAL_SIGNS,
      fields: [{ key: "", value: "", unit: "" }],
      test_date: new Date().toISOString().split("T")[0],
    });
  };

  const addFieldToStructuredData = (index: number) => {
    const currentData = watch(`structured_data.${index}.fields`) || [];
    const newFields = [...currentData, { key: "", value: "", unit: "" }];
    // Update the form with new fields - this would need custom handling
  };

  const steps = [
    { name: "Patient Info", icon: UserIcon },
    { name: "Symptoms", icon: DocumentTextIcon },
    { name: "Medical Data", icon: ChartBarIcon },
    { name: "Images", icon: PhotoIcon },
    { name: "Results", icon: CheckCircleIcon },
  ];

  const detectImageType = (filename: string): string => {
    const name = filename.toLowerCase();
    if (name.includes("retinal") || name.includes("fundus"))
      return ImageType.RETINAL;
    if (name.includes("xray") || name.includes("x-ray")) return ImageType.XRAY;
    if (name.includes("ct") || name.includes("scan")) return ImageType.CT_SCAN;
    if (name.includes("mri")) return ImageType.MRI;
    if (name.includes("ultrasound")) return ImageType.ULTRASOUND;
    return ImageType.GENERAL;
  };

  const getUrgencyBadgeClasses = (urgency: UrgencyLevel) => {
    const classes = {
      [UrgencyLevel.CRITICAL]: "bg-red-100 text-red-800 border-red-200",
      [UrgencyLevel.HIGH]: "bg-orange-100 text-orange-800 border-orange-200",
      [UrgencyLevel.MEDIUM]: "bg-yellow-100 text-yellow-800 border-yellow-200",
      [UrgencyLevel.LOW]: "bg-green-100 text-green-800 border-green-200",
    };
    return `badge border ${classes[urgency]}`;
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-3xl font-bold text-gray-900">New Triage Case</h1>
          <p className="text-gray-600 mt-2">
            Submit a new medical triage case for AI analysis
          </p>
        </motion.div>

        {/* Progress Steps */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <nav aria-label="Progress">
            <ol role="list" className="flex items-center justify-between">
              {steps.map((step, stepIdx) => (
                <li key={step.name} className="relative flex-1">
                  <div className="flex items-center">
                    <div className="flex items-center text-sm font-medium">
                      <span
                        className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                          stepIdx < currentStep
                            ? "bg-medical-600 border-medical-600 text-white"
                            : stepIdx === currentStep
                              ? "border-medical-600 text-medical-600"
                              : "border-gray-300 text-gray-500"
                        }`}
                      >
                        <step.icon className="h-5 w-5" />
                      </span>
                      <span
                        className={`ml-2 ${stepIdx <= currentStep ? "text-gray-900" : "text-gray-500"}`}
                      >
                        {step.name}
                      </span>
                    </div>
                    {stepIdx < steps.length - 1 && (
                      <div
                        className={`ml-4 flex-1 h-0.5 ${
                          stepIdx < currentStep
                            ? "bg-medical-600"
                            : "bg-gray-300"
                        }`}
                      />
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <AnimatePresence mode="wait">
            {/* Step 0: Patient Information */}
            {currentStep === 0 && (
              <motion.div
                key="patient-info"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="card"
              >
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Patient Information
                  </h3>
                  <p className="text-sm text-gray-500">
                    Enter patient details (optional but recommended)
                  </p>
                </div>
                <div className="card-body space-y-4">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="form-label">Patient ID</label>
                      <input
                        type="text"
                        {...register("patient_info.patient_id")}
                        className="form-input"
                        placeholder="P12345"
                      />
                    </div>
                    <div>
                      <label className="form-label">
                        Medical Record Number
                      </label>
                      <input
                        type="text"
                        {...register("patient_info.medical_record_number")}
                        className="form-input"
                        placeholder="MRN-789456"
                      />
                    </div>
                    <div>
                      <label className="form-label">Age</label>
                      <input
                        type="number"
                        {...register("patient_info.age")}
                        className="form-input"
                        placeholder="65"
                        min="0"
                        max="150"
                      />
                    </div>
                    <div>
                      <label className="form-label">Gender</label>
                      <select
                        {...register("patient_info.gender")}
                        className="form-input"
                      >
                        <option value="">Select gender</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                        <option value="prefer_not_to_say">
                          Prefer not to say
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 1: Symptoms and Complaints */}
            {currentStep === 1 && (
              <motion.div
                key="symptoms"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="card"
              >
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Symptoms & Medical History
                  </h3>
                  <p className="text-sm text-gray-500">
                    Describe the patient's condition and symptoms
                  </p>
                </div>
                <div className="card-body space-y-4">
                  <div>
                    <label className="form-label">
                      Chief Complaint <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      {...register("chief_complaint", {
                        required: "Chief complaint is required",
                      })}
                      className={`form-input ${errors.chief_complaint ? "border-red-300" : ""}`}
                      placeholder="e.g., Chest pain, Vision problems, Headache"
                    />
                    {errors.chief_complaint && (
                      <p className="form-error">
                        {errors.chief_complaint.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Detailed Symptoms</label>
                    <textarea
                      {...register("symptoms_text")}
                      rows={4}
                      className="form-input"
                      placeholder="Describe the symptoms in detail, including onset, duration, severity, and any associated symptoms..."
                    />
                  </div>

                  <div>
                    <label className="form-label">Medical History</label>
                    <textarea
                      {...register("medical_history")}
                      rows={3}
                      className="form-input"
                      placeholder="Previous medical conditions, surgeries, medications, allergies..."
                    />
                  </div>

                  <div>
                    <label className="form-label">Additional Notes</label>
                    <textarea
                      {...register("additional_notes")}
                      rows={2}
                      className="form-input"
                      placeholder="Any additional clinical observations or notes..."
                    />
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="form-label">Target Department</label>
                      <select
                        {...register("target_department")}
                        className="form-input"
                      >
                        <option value="">Select department</option>
                        <option value="emergency">Emergency</option>
                        <option value="cardiology">Cardiology</option>
                        <option value="neurology">Neurology</option>
                        <option value="ophthalmology">Ophthalmology</option>
                        <option value="orthopedics">Orthopedics</option>
                        <option value="general_medicine">
                          General Medicine
                        </option>
                      </select>
                    </div>
                    <div>
                      <label className="form-label">Specialty Required</label>
                      <input
                        type="text"
                        {...register("specialty_required")}
                        className="form-input"
                        placeholder="e.g., Cardiologist, Neurologist"
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 2: Structured Medical Data */}
            {currentStep === 2 && (
              <motion.div
                key="structured-data"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="card"
              >
                <div className="card-header">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Medical Data
                      </h3>
                      <p className="text-sm text-gray-500">
                        Add lab results, vital signs, and other structured data
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={addStructuredData}
                      className="btn-primary text-sm"
                    >
                      <PlusIcon className="h-4 w-4 mr-1" />
                      Add Data
                    </button>
                  </div>
                </div>
                <div className="card-body space-y-4">
                  {structuredDataFields.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <ChartBarIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p>No structured data added yet</p>
                      <p className="text-sm text-gray-400 mt-1">
                        Click "Add Data" to include lab results or vital signs
                      </p>
                    </div>
                  ) : (
                    structuredDataFields.map((field, index) => (
                      <div
                        key={field.id}
                        className="border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <select
                              {...register(
                                `structured_data.${index}.data_type`,
                              )}
                              className="form-input w-48"
                            >
                              <option value={StructuredDataType.VITAL_SIGNS}>
                                Vital Signs
                              </option>
                              <option value={StructuredDataType.BLOOD_TEST}>
                                Blood Test
                              </option>
                              <option value={StructuredDataType.LAB_RESULTS}>
                                Lab Results
                              </option>
                              <option
                                value={StructuredDataType.MEDICAL_HISTORY}
                              >
                                Medical History
                              </option>
                              <option value={StructuredDataType.OTHER}>
                                Other
                              </option>
                            </select>
                            <input
                              type="date"
                              {...register(
                                `structured_data.${index}.test_date`,
                              )}
                              className="form-input"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => removeStructuredData(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <XMarkIcon className="h-5 w-5" />
                          </button>
                        </div>

                        <div className="space-y-2">
                          {field.fields.map((_, fieldIndex) => (
                            <div
                              key={fieldIndex}
                              className="grid grid-cols-3 gap-2"
                            >
                              <input
                                {...register(
                                  `structured_data.${index}.fields.${fieldIndex}.key`,
                                )}
                                placeholder="Parameter (e.g., blood_pressure)"
                                className="form-input text-sm"
                              />
                              <input
                                {...register(
                                  `structured_data.${index}.fields.${fieldIndex}.value`,
                                )}
                                placeholder="Value (e.g., 120)"
                                className="form-input text-sm"
                              />
                              <input
                                {...register(
                                  `structured_data.${index}.fields.${fieldIndex}.unit`,
                                )}
                                placeholder="Unit (e.g., mmHg)"
                                className="form-input text-sm"
                              />
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={() => addFieldToStructuredData(index)}
                            className="text-sm text-medical-600 hover:text-medical-800 flex items-center"
                          >
                            <PlusIcon className="h-4 w-4 mr-1" />
                            Add Field
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}

            {/* Step 3: Image Upload */}
            {currentStep === 3 && (
              <motion.div
                key="images"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="card"
              >
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Medical Images
                  </h3>
                  <p className="text-sm text-gray-500">
                    Upload medical images for analysis
                  </p>
                </div>
                <div className="card-body space-y-4">
                  {/* Drag and Drop Zone */}
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                      isDragActive
                        ? "border-medical-400 bg-medical-50"
                        : "border-gray-300 hover:border-medical-400"
                    }`}
                  >
                    <input {...getInputProps()} />
                    <PhotoIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    {isDragActive ? (
                      <p className="text-medical-600">
                        Drop the images here...
                      </p>
                    ) : (
                      <div>
                        <p className="text-gray-600">
                          <span className="font-medium text-medical-600">
                            Click to upload
                          </span>{" "}
                          or drag and drop
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          PNG, JPG, TIFF up to 10MB each
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Uploaded Images */}
                  {uploadedImages.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Uploaded Images ({uploadedImages.length})
                      </h4>
                      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                        {uploadedImages.map((file, index) => (
                          <div key={index} className="relative group">
                            <div className="aspect-w-1 aspect-h-1 bg-gray-100 rounded-lg overflow-hidden">
                              <img
                                src={URL.createObjectURL(file)}
                                alt={`Upload ${index + 1}`}
                                className="w-full h-full object-cover"
                              />
                            </div>
                            <button
                              type="button"
                              onClick={() => removeImage(index)}
                              className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <XMarkIcon className="h-4 w-4" />
                            </button>
                            <p className="mt-2 text-xs text-gray-600 truncate">
                              {file.name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {(file.size / 1024 / 1024).toFixed(1)}MB
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Step 4: Results */}
            {currentStep === 4 && triageResult && (
              <motion.div
                key="results"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="space-y-6"
              >
                {/* Result Summary */}
                <div className="card">
                  <div className="card-header">
                    <div className="flex items-center gap-3">
                      <CheckCircleIcon className="h-6 w-6 text-green-600" />
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          Triage Analysis Complete
                        </h3>
                        <p className="text-sm text-gray-500">
                          Case ID: {triageResult.case_id}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="card-body">
                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                      {/* Triage Score */}
                      <div className="text-center">
                        <div
                          className={`triage-score-display ${
                            triageResult.urgency_level === UrgencyLevel.CRITICAL
                              ? "triage-score-critical"
                              : triageResult.urgency_level === UrgencyLevel.HIGH
                                ? "triage-score-high"
                                : triageResult.urgency_level ===
                                    UrgencyLevel.MEDIUM
                                  ? "triage-score-medium"
                                  : "triage-score-low"
                          }`}
                        >
                          {(triageResult.triage_score! * 100).toFixed(0)}%
                        </div>
                        <p className="text-sm text-gray-600 mt-2">
                          Triage Score
                        </p>
                      </div>

                      {/* Urgency Level */}
                      <div className="text-center">
                        <div
                          className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-semibold ${getUrgencyBadgeClasses(
                            triageResult.urgency_level!,
                          )}`}
                        >
                          {triageResult.urgency_level?.toUpperCase()}
                        </div>
                        <p className="text-sm text-gray-600 mt-2">
                          Priority Level
                        </p>
                      </div>

                      {/* Wait Time */}
                      <div className="text-center">
                        <div className="text-3xl font-bold text-gray-900 p-6">
                          {triageResult.estimated_wait_time === 0
                            ? "IMMEDIATE"
                            : `${triageResult.estimated_wait_time} min`}
                        </div>
                        <p className="text-sm text-gray-600 mt-2">
                          Estimated Wait Time
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                {triageResult.recommendations &&
                  triageResult.recommendations.length > 0 && (
                    <div className="card">
                      <div className="card-header">
                        <h4 className="text-lg font-semibold text-gray-900">
                          Clinical Recommendations
                        </h4>
                      </div>
                      <div className="card-body">
                        <ul className="space-y-2">
                          {triageResult.recommendations.map(
                            (recommendation, index) => (
                              <li
                                key={index}
                                className="flex items-start gap-3"
                              >
                                <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-900">
                                  {recommendation}
                                </span>
                              </li>
                            ),
                          )}
                        </ul>
                      </div>
                    </div>
                  )}

                {/* AI Analysis Results */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {triageResult.synthesized_text_output && (
                    <div className="card">
                      <div className="card-header">
                        <h4 className="text-lg font-semibold text-gray-900">
                          Text Analysis
                        </h4>
                      </div>
                      <div className="card-body">
                        <p className="text-gray-700 text-sm leading-relaxed">
                          {triageResult.synthesized_text_output}
                        </p>
                      </div>
                    </div>
                  )}

                  {triageResult.synthesized_vision_output && (
                    <div className="card">
                      <div className="card-header">
                        <h4 className="text-lg font-semibold text-gray-900">
                          Vision Analysis
                        </h4>
                      </div>
                      <div className="card-body">
                        <p className="text-gray-700 text-sm leading-relaxed">
                          {triageResult.synthesized_vision_output}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex justify-center gap-4">
                  <button
                    type="button"
                    onClick={() => {
                      reset();
                      setUploadedImages([]);
                      setCurrentStep(0);
                      setTriageResult(null);
                    }}
                    className="btn-outline"
                  >
                    Submit Another Case
                  </button>
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="btn-primary"
                  >
                    Print Results
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation Buttons */}
          {currentStep < 4 && (
            <div className="flex justify-between">
              <button
                type="button"
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0}
                className="btn-outline disabled:opacity-50"
              >
                Previous
              </button>

              {currentStep < 3 ? (
                <button
                  type="button"
                  onClick={() => setCurrentStep(currentStep + 1)}
                  className="btn-primary"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <div className="flex items-center gap-2">
                      <div className="spinner-sm" />
                      <span>Processing...</span>
                    </div>
                  ) : (
                    "Submit Case"
                  )}
                </button>
              )}
            </div>
          )}
        </form>
      </div>
    </Layout>
  );
}
