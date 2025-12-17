# User Guide: RAG Chatbot

Welcome to the RAG Chatbot! This guide explains how to use the interactive chat feature in your technical textbook.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Asking Questions](#asking-questions)
3. [Selected Text Mode](#selected-text-mode)
4. [Chat History](#chat-history)
5. [Tips & Tricks](#tips--tricks)
6. [Limitations](#limitations)
7. [FAQ](#faq)

---

## Getting Started

### Opening the Chat

1. Look for the **Chat Icon** (💬) in the bottom-right corner of the textbook
2. Click it to open the chat sidebar
3. You'll see:
   - Chat input field at the bottom
   - Message history in the middle
   - Chat sessions list on the left

### First Message

Type your question in the input field and press **Enter** or click **Send**.

Example questions:
- "What is ROS 2?"
- "How does humanoid design work?"
- "Explain vector embeddings"

The chatbot will:
1. Search the textbook for relevant content
2. Generate an answer based on the retrieved sections
3. Show you sources (chapters/sections) it used

---

## Asking Questions

### Question Tips

✅ **Good questions:**
- Specific and focused: "What are the key differences between ROS 1 and ROS 2?"
- Topic-based: "How does reinforcement learning work in this context?"
- Page reference: "Can you explain the diagram on page 47?"

❌ **Questions to avoid:**
- Too vague: "Tell me everything about robotics"
- Outside textbook scope: "What's the weather today?" (chatbot will say it's not in the textbook)
- Too long: Keep queries under 500 characters

### Multi-Turn Conversations

The chatbot remembers your conversation history!

Example:
1. **You:** "What is ROS 2?"
2. **Bot:** [Explains ROS 2]
3. **You:** "Can you elaborate on that?"
4. **Bot:** [Uses context from previous message to answer]

### Understanding Responses

Responses include:

1. **Answer**: The main response based on your question
2. **Sources**: Chapters/sections used (clickable links)
3. **Confidence**: How relevant the retrieved content was
4. **Latency**: How long the response took (helps troubleshooting)

---

## Selected Text Mode

### How to Use Selected Text

Perfect for understanding specific passages!

**Steps:**

1. Highlight text in the textbook (click and drag)
2. A **"Ask About This"** button appears
3. Click it or type your question in the pop-up
4. The chatbot will answer **using ONLY the selected text**

### Example

> **Selected Text:** "Humanoid robots must balance bipedal locomotion with upper-body manipulation tasks."

**Your Question:** "What challenges are mentioned here?"

**Bot Response:** Based ONLY on the selected text, not the entire book.

### When to Use Selected Text

✅ **Use selected text when:**
- Learning a specific concept in detail
- Verifying the chatbot's understanding of a passage
- Getting explanations of technical terms
- Debugging misunderstandings

❌ **Regular mode when:**
- You need broader context
- Cross-referencing multiple sections
- Building foundational understanding

---

## Chat History

### Accessing Previous Conversations

1. Click the **"Sessions"** button in the chat sidebar
2. You'll see a list of your previous conversations
3. Click any session to restore it
4. All messages and context are restored

### Managing Sessions

**Features:**
- Sessions persist for 24 hours
- Up to 100 sessions stored
- Search sessions by date or first message
- Delete old sessions (optional)

### Exporting Conversations

Want to save a conversation?

```
Right-click chat → Export as PDF/Text
```

This exports:
- All messages
- Sources and citations
- Timestamps

---

## Tips & Tricks

### Better Questions = Better Answers

**Technique 1: Context**
- Bad: "How does this work?"
- Good: "How does the vector embedding process work in the RAG system?"

**Technique 2: Specificity**
- Bad: "Tell me about Chapter 3"
- Good: "What are the main takeaways from the section on humanoid design principles?"

**Technique 3: Follow-ups**
- "Can you elaborate on that?"
- "How does that relate to..."
- "Give an example of..."

### Using Search

Can't find a topic? Use the **Search** feature:
1. Click 🔍 in chat header
2. Type keywords
3. Chat finds relevant chapters

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send message |
| `Esc` | Close chat |
| `Ctrl+K` | Open search |
| `↑/↓` | Previous/next message |

---

## Limitations

### What the Chatbot Can Do

✅ Answer questions about textbook content
✅ Provide detailed explanations
✅ Cross-reference multiple sections
✅ Clarify technical concepts
✅ Give examples from the book

### What the Chatbot Cannot Do

❌ Answer questions outside the textbook
❌ Provide real-time information
❌ Give professional advice (always consult experts)
❌ Access external websites or databases
❌ Remember conversations beyond 24 hours

### If It Can't Answer

If the chatbot says: **"I don't have information about that in the textbook"**

This means:
1. The topic isn't covered in this book
2. The phrasing didn't match textbook content
3. Try rephrasing your question

**Solution:** Try:
- Different keywords
- Simpler language
- Asking about related concepts
- Using selected text mode

---

## FAQ

### Q: Is my chat data private?

**A:** Yes! Your conversations are:
- Encrypted in transit (HTTPS)
- Stored securely on servers
- Never used to train models
- Deleted after 24 hours

### Q: Why is the response slow?

**A:** Response time depends on:
- Question complexity (typically 3-6 seconds)
- API availability (sometimes 5-10s)
- Network latency

If consistently slow:
1. Check your internet connection
2. Try a simpler question
3. Refresh the page
4. Contact support

### Q: Can I use this offline?

**A:** No, the chatbot requires internet. It needs to:
- Search the vector database
- Call the language model API
- Retrieve from the database

### Q: What if I find an error?

**A:** Please report it!
1. Click **Report Issue** in chat menu
2. Include:
   - Your question
   - The incorrect response
   - What was wrong
3. We'll fix it in the next update

### Q: Can I access my chat history?

**A:** Yes! Sessions are stored for 24 hours. After that, they're deleted for privacy.

To keep a conversation:
- Export it to PDF/text
- Screenshot key responses
- Save to your notes app

### Q: How many questions can I ask?

**A:** You get:
- **10 questions per minute** (prevents spam)
- **1000 questions per day** per IP address (fair usage)

Limits reset automatically.

### Q: What if I have a feature request?

**A:** Great! Please:
1. Click **Feedback** in chat menu
2. Describe your idea
3. We review all suggestions

Popular requests we've added:
- Selected text mode
- Chat history export
- Session management
- Keyboard shortcuts

### Q: How accurate is the chatbot?

**A:** Accuracy depends on:
- How well your question matches textbook content
- Relevance of retrieved sections
- Question clarity

We target **90%+ accuracy** for questions covered in the book.

### Q: Can I share conversations?

**A:** Not directly through chat, but you can:
1. Export conversation to PDF
2. Share the PDF file
3. Others can view your Q&A

### Q: Is there a mobile app?

**A:** The chat works on mobile browsers! Features:
- Same functionality as desktop
- Touch-friendly interface
- Works on iPhone, Android, tablets

Optimized for: Safari, Chrome, Firefox

---

## Getting Help

### Still Have Questions?

1. **Check the FAQ** above
2. **Try the Help Center** (click **?** in chat)
3. **Email support**: support@example.com
4. **Report a bug**: Click **Report Issue** in chat

### Feedback

We'd love to hear from you!
- What's working well?
- What could be better?
- Feature requests?

Click **Feedback** → **Send** to share your thoughts.

---

## Tips for Learning

### Combine Reading + Chat

**Best approach:**
1. Read textbook section
2. Ask clarifying questions via chat
3. Explore related topics via follow-ups
4. Export conversation for notes

### Build Knowledge Progressively

Don't ask: "Tell me everything about Topic X"

Instead:
1. "What is Topic X?"
2. "What are the key principles?"
3. "How does it relate to Y?"
4. "Can you give an example?"

### Use Selected Text for Deep Dives

When you want to truly understand a passage:
1. Highlight the text
2. Ask specific questions about it
3. Chat focuses ONLY on that passage
4. Great for exam preparation

---

**Happy learning! 🚀**

*The RAG Chatbot is here to help you get the most out of this textbook. Don't hesitate to ask questions!*
