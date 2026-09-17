"use client";

import { useParams } from "next/navigation";

import { InterviewSessionWorkspace } from "@/components/features/interview/interview-session-workspace";

export default function InterviewSessionPage() {
  const params = useParams<{ id: string }>();
  return <InterviewSessionWorkspace interviewId={params.id} />;
}
