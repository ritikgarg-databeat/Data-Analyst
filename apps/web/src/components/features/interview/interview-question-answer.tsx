"use client";

import { useState } from "react";
import type { AnswerInterviewQuestionRequest, ExcelSheet, InterviewQuestionDetail } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { SqlEditor } from "@/components/features/sql-lab/sql-editor";
import { PythonCellEditor } from "@/components/features/python-lab/python-cell-editor";
import { ExcelGrid } from "@/components/features/interview/excel-grid";

const EXECUTION_TYPES = new Set(["SQL", "DBT"]);
const CONCEPTUAL_TYPES = new Set(["MULTIPLE_CHOICE", "TRUE_FALSE"]);

interface InterviewQuestionAnswerProps {
  question: InterviewQuestionDetail;
  onSubmit: (payload: AnswerInterviewQuestionRequest) => void;
  isSubmitting: boolean;
}

export function InterviewQuestionAnswer({ question, onSubmit, isSubmitting }: InterviewQuestionAnswerProps) {
  const [queryText, setQueryText] = useState(question.sql_starter_query ?? "");
  const [codeText, setCodeText] = useState(question.python_starter_code ?? "");
  const [freeText, setFreeText] = useState("");
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [rubricSelections, setRubricSelections] = useState<Set<string>>(new Set());
  const [sheets, setSheets] = useState<ExcelSheet[]>(question.excel_starter_sheets);

  // No effect needed to reset this state when the question changes — the
  // parent renders this component with `key={attempt.id}`, so a new question
  // remounts it fresh, and these useState initializers above already read
  // from that new question's own starter content.

  function toggleRubric(criterion: string) {
    setRubricSelections((prev) => {
      const next = new Set(prev);
      if (next.has(criterion)) next.delete(criterion);
      else next.add(criterion);
      return next;
    });
  }

  function handleSubmit() {
    if (question.exercise_type === "SQL" || question.exercise_type === "DBT") {
      onSubmit({ submitted_query: queryText });
      return;
    }
    if (question.exercise_type === "PYTHON") {
      onSubmit({ submitted_code: codeText });
      return;
    }
    if (question.exercise_type === "EXCEL") {
      onSubmit({ submitted_sheets: sheets });
      return;
    }
    if (CONCEPTUAL_TYPES.has(question.exercise_type)) {
      onSubmit({ submitted_answer: selectedChoice ?? "" });
      return;
    }
    // Free-text / rubric-scored (BUSINESS_REASONING, DATA_INTERPRETATION,
    // MODELING, INTERVIEW_RESPONSE (Behavioral), SHORT_ANSWER).
    onSubmit({
      submitted_answer: freeText,
      rubric_selections: question.rubric.length > 0 ? Array.from(rubricSelections) : undefined,
    });
  }

  const canSubmit = (() => {
    if (question.exercise_type === "SQL" || question.exercise_type === "DBT") return queryText.trim().length > 0;
    if (question.exercise_type === "PYTHON") return codeText.trim().length > 0;
    if (question.exercise_type === "EXCEL") return true;
    if (CONCEPTUAL_TYPES.has(question.exercise_type)) return Boolean(selectedChoice);
    return freeText.trim().length > 0;
  })();

  return (
    <div className="flex flex-col gap-4">
      {EXECUTION_TYPES.has(question.exercise_type) ? (
        <SqlEditor value={queryText} onChange={setQueryText} height={260} />
      ) : question.exercise_type === "PYTHON" ? (
        <PythonCellEditor value={codeText} onChange={setCodeText} height={260} />
      ) : question.exercise_type === "EXCEL" ? (
        <ExcelGrid sheets={sheets} onChange={setSheets} checkCells={question.excel_check_cells} />
      ) : question.choices && question.choices.length > 0 ? (
        <fieldset className="flex flex-col gap-2">
          <legend className="sr-only">Answer choices</legend>
          {question.choices.map((choice) => (
            <label
              key={choice}
              className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm has-[:checked]:border-primary has-[:checked]:bg-primary/5"
            >
              <input
                type="radio"
                name="choice"
                value={choice}
                checked={selectedChoice === choice}
                onChange={() => setSelectedChoice(choice)}
                className="size-4"
              />
              {choice}
            </label>
          ))}
        </fieldset>
      ) : (
        <Textarea
          value={freeText}
          onChange={(e) => setFreeText(e.target.value)}
          rows={8}
          placeholder="Write your answer here..."
          aria-label="Your answer"
        />
      )}

      {question.rubric.length > 0 && !EXECUTION_TYPES.has(question.exercise_type) && question.exercise_type !== "PYTHON" && question.exercise_type !== "EXCEL" ? (
        <div className="rounded-xl border border-border bg-muted/20 p-3">
          <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Self-assess: which of these does your answer satisfy?
          </p>
          <ul className="flex flex-col gap-1.5">
            {question.rubric.map((criterion) => (
              <li key={criterion.criterion}>
                <label className="flex cursor-pointer items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={rubricSelections.has(criterion.criterion)}
                    onChange={() => toggleRubric(criterion.criterion)}
                    className="mt-0.5 size-4"
                  />
                  <span>
                    {criterion.criterion} <span className="text-muted-foreground">({criterion.points} pts)</span>
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="flex justify-end">
        <Button onClick={handleSubmit} disabled={!canSubmit || isSubmitting}>
          {isSubmitting ? "Submitting..." : "Submit Answer"}
        </Button>
      </div>
    </div>
  );
}
