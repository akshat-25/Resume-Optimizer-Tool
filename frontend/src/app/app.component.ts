import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

interface ScoreBreakdown {
  overall: number;
  ats: number;
  keyword_match: number;
  semantic_match: number;
  impact: number;
  clarity: number;
  completeness: number;
}

interface Finding {
  severity: string;
  issue: string;
  why_it_matters: string;
  action: string;
}

interface Suggestion {
  section: string;
  before: string;
  after: string;
  why_it_is_better: string;
  needs_verification: boolean;
  questions: string[];
}

interface AnalyzeResponse {
  resume: any;
  job_description: any;
  scores: ScoreBreakdown;
  matched_keywords: string[];
  missing_keywords: string[];
  ats_findings: Finding[];
  resume_findings: Finding[];
  suggestions: Suggestion[];
  llm_available: boolean;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private readonly apiBase = 'http://localhost:8000/api';

  resumeText = '';
  jobDescription = '';
  model = 'qwen3:8b';
  useLlm = true;
  isAnalyzing = false;
  isDownloading = false;
  error = '';
  result: AnalyzeResponse | null = null;

  constructor(private readonly http: HttpClient) {}

  analyze(): void {
    this.error = '';
    this.result = null;

    if (!this.resumeText.trim() || !this.jobDescription.trim()) {
      this.error = 'Add both resume text and a job description before analyzing.';
      return;
    }

    this.isAnalyzing = true;
    this.http.post<AnalyzeResponse>(`${this.apiBase}/analyze`, {
      resume_text: this.resumeText,
      job_description: this.jobDescription,
      model: this.model,
      use_llm: this.useLlm
    }).subscribe({
      next: (response) => {
        this.result = response;
        this.isAnalyzing = false;
      },
      error: (err) => {
        console.error('Analysis error:', err);
        this.error = 'Could not reach the FastAPI backend. Start it on http://localhost:8000 and try again.';
        this.isAnalyzing = false;
      }
    });
  }

  onResumeFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }

    const data = new FormData();
    data.append('file', file);

    this.http.post<{ text: string }>(`${this.apiBase}/resume/extract-text`, data).subscribe({
      next: (response) => {
        this.resumeText = response.text;
      },
      error: (err) => {
        console.error('File extraction error:', err);
        this.error = 'Could not extract text from that file. Try pasting the resume text directly.';
      }
    });
  }

  scoreItems(): { label: string; value: number }[] {
    if (!this.result) {
      return [];
    }

    return [
      { label: 'Overall', value: this.result.scores.overall },
      { label: 'ATS', value: this.result.scores.ats },
      { label: 'Keywords', value: this.result.scores.keyword_match },
      { label: 'Semantic match', value: this.result.scores.semantic_match },
      { label: 'Impact', value: this.result.scores.impact },
      { label: 'Clarity', value: this.result.scores.clarity },
      { label: 'Completeness', value: this.result.scores.completeness }
    ];
  }

  downloadResume(): void {
    if (!this.result) {
      return;
    }

    this.isDownloading = true;
    this.http.post(`${this.apiBase}/resume/download-pdf`, this.result, {
      responseType: 'blob'
    }).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'optimized_resume.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        this.isDownloading = false;
      },
      error: (err) => {
        console.error('Download error:', err);
        this.error = 'Failed to generate the optimized resume file. Check console for details.';
        this.isDownloading = false;
      }
    });
  }
}
