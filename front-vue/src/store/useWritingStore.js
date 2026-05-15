import { defineStore } from "pinia";
import { ref } from "vue";
import { request } from "@/utils/request";

export const useWritingStore = defineStore("writing", () => {
  const sessions = ref([]);
  const currentSession = ref(null);
  const messages = ref([]);
  const streaming = ref(false);
  const streamingReasoning = ref("");
  const streamingContent = ref("");
  const lastRefs = ref([]);

  async function fetchSessions(novelId) {
    sessions.value = await request({ url: `/api/novels/${novelId}/sessions`, method: "get" }) || [];
  }

  async function createSession(novelId, title = "新对话") {
    const data = await request({ url: `/api/novels/${novelId}/sessions`, method: "post", data: { title } });
    sessions.value.unshift(data);
    currentSession.value = data;
    messages.value = [];
    return data;
  }

  async function fetchMessages(sessionId) {
    messages.value = await request({ url: `/api/sessions/${sessionId}/messages`, method: "get" }) || [];
  }

  function addUserMessage(content) {
    messages.value.push({ role: "user", content, reasoning_content: "" });
  }

  function addAssistantMessage(content, reasoning) {
    messages.value.push({ role: "assistant", content, reasoning_content: reasoning });
  }

  async function* generateStream(sessionId, message, chapterId = null) {
    streaming.value = true;
    streamingReasoning.value = "";
    streamingContent.value = "";

    const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const resp = await fetch(`${baseUrl}/api/sessions/${sessionId}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, chapter_id: chapterId }),
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let currentEvent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            const eventType = currentEvent || "data";
            if (eventType === "reasoning") {
              streamingReasoning.value += data.content || "";
            } else if (eventType === "content" || eventType === "data") {
              if (data.content) streamingContent.value += data.content;
            } else if (eventType === "done") {
              if (data.refs) lastRefs.value = data.refs;
            }
            yield { type: eventType, data };
          } catch (e) { /* skip malformed */ }
        }
      }
    }
    streaming.value = false;
  }

  function reset() {
    sessions.value = [];
    currentSession.value = null;
    messages.value = [];
    streaming.value = false;
    streamingReasoning.value = "";
    streamingContent.value = "";
    lastRefs.value = [];
  }

  return {
    sessions, currentSession, messages, streaming, streamingReasoning, streamingContent, lastRefs,
    fetchSessions, createSession, fetchMessages, addUserMessage, addAssistantMessage, generateStream, reset,
  };
});
