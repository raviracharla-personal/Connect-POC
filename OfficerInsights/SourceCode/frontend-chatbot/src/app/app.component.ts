import {
  Component,
  NgZone,
  ViewChild,
  ElementRef,
  OnInit,
  OnDestroy,
} from "@angular/core";
import { ApiService, Message, ApiResponse } from "./services/api.service";
import { Subscription } from "rxjs";

@Component({
  selector: "app-root",
  templateUrl: "./app.component.html",
  styleUrls: ["./app.component.css"],
})
export class AppComponent {
  @ViewChild("inputTextArea") private inputTextAreaElement!: ElementRef;
  @ViewChild("chatAnchor") private chatAnchor!: ElementRef;

  userInput: string = "";
  messages: Message[] = [];
  finalReport: any = null;
  isLoading: boolean = false;
  isListening: boolean = false;
  loadingMessage: string = "Processing your request...";
  reportTitle: string = "Final Report";
  private mediaStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private apiSubscription = new Subscription();

  constructor(private apiService: ApiService, private zone: NgZone) {}

  sendTextForProcessing(): void {
    const queryText = this.userInput.trim();
    if (!queryText || this.isLoading) return;

    this.zone.run(() => {
      this.isLoading = true;
      this.loadingMessage = "Processing your request...";
      this.finalReport = null;
      this.messages.push({ role: "user", content: queryText });
      this.userInput = "";
      this.scrollToBottom(); 
    });

    // --- (Your API call logic here) ---
    const history = this.messages.slice(0, -1);
    this.apiSubscription = this.apiService
      .processText(queryText, history)
      .subscribe({
        next: (response) => {
          this.zone.run(() => {
            this.isLoading = false;
            if (response.status === 'error' && response.intent === 'unsupported') {
              // Handle the unsupported intent error from the AI
              const errorMessage = response.data?.errorMessage || "I'm sorry, I can't help with that. Please provide a traffic offence or investigation report.";
              this.messages.push({ role: 'assistant', content: errorMessage, isError: true }); // Add an isError flag          
            } else if (
                response.status === "complete" &&
                response.data &&
                response.intent
              ) {
                this.finalReport = response.data;
                this.reportTitle = this.formatIntentToTitle(response.intent); // Set the dynamic title
                this.messages.push({
                  role: "assistant",
                  content: "Report generated successfully.",
                });
              } else if (response.status === "incomplete") {
                const prompt =
                  response.prompt ||
                  "I need more information, but I'm unable to formulate a question.";
                this.messages.push({ role: "assistant", content: prompt });
              }
              this.scrollToBottom(); 
              this.focusOnInput();
          });
        },
        error: (err) => {
          this.zone.run(() => {
            this.isLoading = false;
            this.messages.push({ role: 'assistant', content: `Error: ${err.error?.detail || 'Could not connect to server.'}` });
            this.scrollToBottom();
          });

        },
      });
  }

  reset(): void {
    this.cancelRequest();
    this.userInput = "";
    this.messages = [];
    this.finalReport = null;
    this.isLoading = false;
    if (this.isListening) {
      this.cancelRecording();
    }
  }

  private scrollToBottom(): void {
    // A brief timeout gives Angular time to render the new message/anchor before we scroll.
    setTimeout(() => {
      try {
        if (this.chatAnchor) {
          this.chatAnchor.nativeElement.scrollIntoView({
            behavior: "smooth",
            block: "end",
          });
        }
      } catch (err) {
        console.error("Could not scroll to bottom:", err);
      }
    }, 100);
  }

  private formatIntentToTitle(intent: string): string {
    if (!intent) return "Final Report";
    // Converts "create_traffic_offence_report" to "Traffic Offence Report"
    return intent
      .replace("create_", "")
      .replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }
  handleKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      this.sendTextForProcessing();
    }
  }
  private focusOnInput(): void {
    try {
      setTimeout(() => {
        if (this.inputTextAreaElement) {
          this.inputTextAreaElement.nativeElement.focus();
        }
      }, 0);
    } catch (err) {}
  }
  cancelRequest(): void {
    if (this.apiSubscription) {
      this.apiSubscription.unsubscribe();
    }
    this.isLoading = false;
    this.messages.push({ role: "assistant", content: "Request cancelled." });
    this.scrollToBottom();
    this.focusOnInput();
  }
  toggleListen(): void {
    if (this.isListening) {
      this.stopAndProcessRecording();
    } else {
      this.startRecording();
    }
  }
  cancelRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
      this.mediaRecorder.onstop = null;
      this.mediaRecorder.stop();
    }
    this.releaseMicrophone();
    this.isListening = false;
    this.audioChunks = [];
  }
  
  private playAudioBlob(blob: Blob): void {
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.play();
  }

  private stopAndProcessRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
      this.mediaRecorder.stop();
    }
    this.isListening = false;
  }
  private releaseMicrophone(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
  }
  async startRecording(): Promise<void> {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
    } catch (err) {
      alert("Microphone access is required for the voice feature. Please check browser permissions.");
      return;
    }
    this.audioChunks = [];
    this.zone.run(() => {
      this.isListening = true;
    });
    this.mediaRecorder = new MediaRecorder(this.mediaStream, {
      mimeType: "audio/webm;codecs=opus",
    });
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.audioChunks.push(event.data);
    };
    this.mediaRecorder.onstop = () => {
      const audioBlob = new Blob(this.audioChunks, { type: "audio/webm" });
      this.releaseMicrophone();
      if (audioBlob.size > 1000) 
      {
        this.playAudioBlob(audioBlob);

        this.transcribeRecording(audioBlob) 
      }
      else {
        console.warn("Recording was too short or silent.");
      };
    };
    this.mediaRecorder.start();
  }

  private transcribeRecording(audioBlob: Blob): void {
    this.zone.run(() => {
      this.isLoading = true;
      this.loadingMessage = "Transcribing your audio...";
      this.scrollToBottom();
    });
    this.apiSubscription = this.apiService
      .transcribeAudio(audioBlob)
      .subscribe({
        next: (response) => {
          this.zone.run(() => {
            this.isLoading = false;
            this.userInput = response.transcript;
          });
        },
        error: (err) => {
          this.zone.run(() => {
            this.isLoading = false;
            this.messages.push({
              role: "assistant",
              content: `Error during transcription: ${err.error?.detail || 'Could not process audio.'}`,
            });
            this.scrollToBottom();
            this.focusOnInput();
          });
        },
      });
  }
}
