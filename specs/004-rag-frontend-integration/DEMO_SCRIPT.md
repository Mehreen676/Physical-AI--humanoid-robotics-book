# Demo Script: RAG Chat Widget

**For Hackathon Judges**

This script demonstrates the key features of the RAG Chat Widget for evaluators.

---

## Demo Setup (2 minutes)

### Prerequisites
- Backend deployed to Railway/Heroku or running locally
- Frontend deployed to GitHub Pages OR running locally
- Backend health check passed: `curl https://your-backend.com/health`

### Demo URLs
- **Live Site**: https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
- **Or Local**: http://localhost:3000 (if running locally)

---

## Demo Walkthrough (5 minutes)

### Feature 1: Basic Query Interface (1 minute)

**Goal**: Show that users can ask questions and get answers

**Steps**:
1. Open chat widget on any textbook page
2. Point out the clean, minimal interface
   - Simple text input
   - Send button
   - Character counter (0-5000 chars)
3. Type first query:
   ```
   What is humanoid robotics?
   ```
4. Click Send (or press Ctrl+Enter)
5. Wait 2-5 seconds for response
6. Show the response with formatting

**Expected Outcome**:
- ✅ Response appears in chat
- ✅ Time to response < 5 seconds
- ✅ Answer is relevant to question

---

### Feature 2: Sources & Confidence (1 minute)

**Goal**: Show that answers are sourced from the textbook

**Steps**:
1. Look at the displayed response
2. Point out the confidence score:
   - Green bar (≥80%): High confidence
   - Orange bar (60-80%): Medium confidence
   - Red bar (<60%): Low confidence
3. Scroll down to see "Sources" section
4. Count the source links (typically 3-5)
5. Click one source link
   - Opens textbook page in new tab
   - Shows where the answer came from
6. Go back to chat

**Expected Outcome**:
- ✅ Confidence score displayed with color coding
- ✅ Sources are clickable and accurate
- ✅ Each source links to actual textbook content

---

### Feature 3: Selected-Text Query (1 minute)

**Goal**: Show the unique selected-text feature

**Steps**:
1. Highlight a sentence in the textbook:
   ```
   "Select this text from the humanoid robotics chapter"
   ```
2. Watch for blue banner to appear: "Selected: ..."
3. Click "Ask about this" button
4. Chat widget pre-fills with selected text
5. Notice green banner: "Context: Using selected text"
6. Modify the question:
   ```
   "What is the significance of this concept?"
   ```
7. Click Send
8. Show response uses the selected text as context

**Expected Outcome**:
- ✅ Text selection detected automatically
- ✅ Blue/green banners appear without clicking anything
- ✅ Query pre-filled with selected text
- ✅ Response is contextually relevant to highlighted text

---

### Feature 4: Chat History (30 seconds)

**Goal**: Show conversation persistence

**Steps**:
1. Point out all previous questions and answers in chat
2. Scroll up to see full conversation history
3. Show stats at bottom:
   - Number of questions asked
   - Average response time
   - Average confidence

**Expected Outcome**:
- ✅ Messages stay in order
- ✅ Both user and assistant messages visible
- ✅ Statistics accurate and useful

---

### Feature 5: Error Handling (30 seconds)

**Goal**: Show graceful error handling

**Steps**:
1. Clear chat (button in header)
2. Try to submit empty query:
   - Click Send without text
   - Error message appears: "Please enter a question"
3. Try too-short query:
   - Type "ab"
   - Error: "Question must be at least 3 characters"
4. Show these are helpful, user-friendly messages

**Expected Outcome**:
- ✅ Validation errors are clear
- ✅ No technical jargon or stack traces
- ✅ User can easily fix and retry

---

## Optional Deep Dives (If Time Allows)

### Load Time Performance
```bash
# In DevTools (F12) → Network tab
# Filter to "XHR" requests
# Show response time for /chat endpoint: ~2-5 seconds
```

### Architecture Explanation
```
Frontend (GitHub Pages)
    ↓ HTTPS/CORS
Backend (FastAPI)
    ↓
Vector Store (Qdrant)
    ↓
LLM (OpenAI/OpenRouter)
```

### Component Quality
- Open DevTools (F12) → Console
- Show no JavaScript errors
- Show responsive design on mobile
- Click "Matched Chunks" to see retrieved documents

---

## Talking Points for Judges

### Technical Achievements
✅ **Full-Stack Integration**
- Frontend React/TypeScript on GitHub Pages
- Backend FastAPI with CORS configuration
- Real-time HTTP communication
- Vector similarity search with LLM synthesis

✅ **User Experience**
- Minimal, clean interface
- Selected-text detection (unique feature)
- Contextually relevant responses
- Confidence scoring

✅ **Production Readiness**
- Deployed to GitHub Pages (no backend hosting needed)
- Configurable backend URLs
- Comprehensive error handling
- Mobile responsive design

✅ **Developer Experience**
- Clear code structure (components, hooks, services)
- 24+ test cases for reliability
- TypeScript for type safety
- Well-documented architecture

### Key Features Demonstrated
1. **Query Interface**: Users ask questions naturally
2. **Answer Synthesis**: Backend combines retrieval + LLM
3. **Source Attribution**: Every answer is sourced
4. **Selected-Text**: Unique RAG feature for textbooks
5. **Deployment**: Works on GitHub Pages (no backend hosting)

---

## FAQ for Judges

**Q: How does the backend know which textbook content is relevant?**
A: The backend uses Qdrant vector similarity search with the query embeddings. Relevant chunks are ranked by similarity score and sent to the LLM.

**Q: Why show confidence scores?**
A: Confidence indicates how certain the answer is. Low scores might need fact-checking, while high scores are more reliable.

**Q: Is authentication required?**
A: No, the chat is completely public. No login needed for judges to test.

**Q: Can this work on other textbooks?**
A: Yes, the architecture is generic. Any textbook with embeddings in Qdrant can use this widget.

**Q: What happens if the backend is down?**
A: The widget shows "Chat service unavailable" error. The site still loads; just the chat doesn't work.

**Q: How fast is the response time?**
A: Typical: 2-5 seconds depending on query complexity and backend load.

---

## Demo Timing

| Section | Time |
|---------|------|
| Setup & Introduction | 1 min |
| Feature 1: Basic Query | 1 min |
| Feature 2: Sources | 1 min |
| Feature 3: Selected-Text | 1 min |
| Feature 4: History | 0.5 min |
| Feature 5: Errors | 0.5 min |
| Q&A | 1 min |
| **Total** | **6 minutes** |

---

## Backup Queries (If Main Ones Fail)

These alternative queries can be used if specific textbook content isn't available:

```
"What are the main challenges in humanoid robot development?"
"How do actuators work in robotic systems?"
"What is machine learning in robotics?"
"Explain inverse kinematics"
"What are the safety requirements for robots?"
```

---

## Troubleshooting During Demo

| Issue | Solution |
|-------|----------|
| **Backend timeout** | Pre-load one response before demo |
| **No sources appear** | Try different query with more matches |
| **Widget not visible** | Refresh page or check console errors (F12) |
| **Selected-text not detecting** | Highlight slower, wait for banner |
| **CORS error** | Backend URL misconfigured, show offline slide |

---

## Success Criteria for Judges

✅ Chat widget loads without errors
✅ Query submission works
✅ Response appears within 5 seconds
✅ Sources are displayed with links
✅ Selected-text feature detects text
✅ Pre-filled query with context
✅ Error handling works gracefully
✅ Mobile responsive layout
✅ No authentication required
✅ Deployed on live GitHub Pages

---

## What Judges Are Looking For

1. **Functionality**: Does it work? (Yes ✅)
2. **User Experience**: Is it easy to use? (Yes, minimal interface ✅)
3. **Integration**: How well is it integrated? (Embedded in textbook ✅)
4. **Uniqueness**: What makes it special? (Selected-text feature ✅)
5. **Deployment**: Can it scale? (GitHub Pages + scalable backend ✅)
6. **Code Quality**: Is the code clean? (TypeScript, tests, documentation ✅)

---

## Post-Demo Resources

Hand these to judges:
- **README.md** - Architecture and implementation details
- **QUICKSTART.md** - How to set it up locally
- **DEPLOYMENT_GUIDE.md** - How to deploy
- **GitHub Repo** - Source code

---

**Demo Ready!** 🎉

Show judges how RAG + Textbooks = Better Learning Experience
