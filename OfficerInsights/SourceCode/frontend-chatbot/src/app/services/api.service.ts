// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  isError?: boolean;
}

export interface ApiResponse {
  status: 'complete' | 'incomplete' | 'error';
  intent?: string;
  data?: any;
  prompt?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // private audioBackendUrl = 'http://localhost:8000/api/process-audio';
  // private backendUrl = 'http://localhost:8000/api/process-text';
  // Use the proxied relative paths
  private transcribeUrl = `${environment.apiUrl}/api/transcribe-audio`; //`${environment.apiUrl}/api/process-query`;
  // private processTextUrl = '/api/process-text';
  private processTextUrl = `${environment.apiUrl}/api/process-text`;

  constructor(private http: HttpClient) { }

  transcribeAudio(audioBlob: Blob): Observable<{ transcript: string }> {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'audio.wav');
    return this.http.post<{ transcript: string }>(this.transcribeUrl, formData);
  }

  // processAudio(audioBlob: Blob, history: Message[]): Observable<ApiResponse> {
  //   const formData = new FormData();
  //   formData.append('audio_file', audioBlob, 'audio.webm'); // Send as a file
  //   // Note: FastAPI needs complex objects like arrays to be sent as a string in FormData
  //   formData.append('history', JSON.stringify(history)); // Send history as a JSON string

  //   return this.http.post<ApiResponse>(this.audioBackendUrl, formData);
  // }

  processText(text: string, history: Message[]): Observable<ApiResponse> {
    const payload = { text, history };
    return this.http.post<ApiResponse>(this.processTextUrl, payload);
  }
}