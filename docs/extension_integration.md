# SCK Extension Integration Guide

This document explains how the Chrome extension should communicate with the SCK backend.

The extension is intended to be the primary SCK user experience:
- capture messages in real time
- send them to the backend
- receive a structured continuation context
- display or copy the context in the popup UI

---

## 1) Backend Overview

The SCK backend is a FastAPI application with:

- parsing support for ChatGPT, Claude, share links, raw text, and extension payloads
- session persistence in MySQL
- context persistence in MySQL
- structured continuation generation strategies
- Gemini-powered AI continuation strategies

---

## 2) Local Backend Startup

### 2.1 Activate the virtual environment

From the project root:

```bash
venv\Scripts\activate.bat