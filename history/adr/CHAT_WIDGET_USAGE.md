# Chat Widget User Guide

How to use the embedded AI chat assistant in the Physical AI & Humanoid Robotics Textbook.

## Overview

The chat assistant helps you understand the book content by answering questions. It can:

- Answer questions about the entire book
- Explain specific passages you highlight
- Provide citations to source material
- Remember your conversation within a session

## Getting Started

### Opening the Chat

Look for the chat icon in the bottom-right corner of any book page:

```
┌─────────────────────────────────┐
│  Book Content                   │
│                                 │
│                         ┌────┐  │
│                         │💬 │  │  ← Click here
│                         └────┘  │
└─────────────────────────────────┘
```

Click the icon to open the chat panel.

### First Interaction

When you open the chat for the first time:

1. Chat panel slides out from the right
2. You see a welcome message
3. Input field is ready for your question
4. A session ID is generated automatically

## Asking Questions

### Full-Book Questions

Use this mode to ask questions about the entire textbook.

**Examples**:
- "What is ROS 2?"
- "Explain the difference between Physical AI and traditional robotics"
- "What sensors are used in humanoid robots?"
- "How does DDS work in ROS 2?"

**How to ask**:
1. Open chat widget
2. Type your question in the input field
3. Press Enter (or click the send button)
4. Wait for the response (typically 2-5 seconds)

**Response includes**:
- Main answer (formatted with markdown)
- Source citations (expandable)
- Chapter and section references

### Selected-Text Questions

Use this mode to ask questions about a specific passage you've highlighted.

**Examples**:
- "Explain this in simpler terms"
- "What does this mean?"
- "How does this relate to the previous section?"
- "Can you provide an example?"

**How to ask**:
1. **Highlight text** on the page you want to ask about
   - Click and drag to select the text
   - Must be at least 10 characters
   - Maximum 2000 characters
2. Open the chat widget
3. You'll see a **blue badge** showing your selected text
4. Type your question in the input field
5. Press Enter

**What happens**:
- Your question is answered based **only** on the selected text
- The AI won't use information from other parts of the book
- This gives you focused, precise answers

**Clearing selection**:
- Click the X button on the blue badge
- Or ask your question (selection clears automatically)

## Understanding Responses

### Answer Format

Answers are formatted with markdown:

- **Bold text**: Important terms or concepts
- *Italic text*: Emphasis
- `Code`: Technical terms or commands
- Lists: Organized information
- Links: References to other sections (if enabled)

### Citations

Every answer includes source citations:

```
┌───────────────────────────────────────┐
│ Answer: ROS 2 is the next generation  │
│ of the Robot Operating System...      │
│                                       │
│ ▼ Sources (3)                         │
│   • Chapter 1 - Section 1.2           │
│     "ROS 2 is the next generation..." │
│     Relevance: 85%                    │
│                                       │
│   • Chapter 2 - Section 2.1           │
│     "Key improvements include..."     │
│     Relevance: 78%                    │
└───────────────────────────────────────┘
```

**How to read citations**:
- **Chapter/Section**: Where the information is from
- **Text snippet**: Preview of the source content
- **Relevance**: How well this source matches your question (higher = better)

**Expanding citations**:
- Click "Sources (N)" to expand the list
- Click again to collapse

### Refusals

Sometimes the AI cannot answer your question:

**Example refusal**:
> "I cannot answer this question based on the book content provided. This information may not be covered in the textbook."

**Why this happens**:
- Question is outside the book's scope
- Topic not covered in the textbook
- Question too vague or ambiguous

**What to do**:
- Rephrase your question
- Ask about a different topic
- Check if the topic is in the book's table of contents
- Try selecting relevant text first

## Conversation Features

### Session Memory

The chat remembers your conversation:

- Previous questions and answers
- Conversation context
- Your preferences

**How it works**:
- Session starts when you first open chat
- Lasts until you close the browser tab
- Refresh the page = new session (conversation cleared)

**Follow-up questions**:

You can ask follow-up questions without repeating context:

```
You: What is ROS 2?
AI: ROS 2 is the next generation...

You: What are the main improvements?
AI: [Understands you mean "improvements in ROS 2"]

You: How does it compare to ROS 1?
AI: [Knows context from previous questions]
```

### Message History

Your conversation is displayed chronologically:

- **Your messages**: Blue bubbles on the right
- **AI messages**: Gray bubbles on the left
- **Timestamps**: When each message was sent
- **Auto-scroll**: Newest message always visible

### Clearing Chat

To start a new conversation:

1. Refresh the page (clears session)
2. Or continue in the same session (context maintained)

## Tips for Better Answers

### Be Specific

❌ Bad: "Tell me about robots"
✅ Good: "What sensors are used in humanoid robots?"

### Use Key Terms

❌ Bad: "How does that thing work?"
✅ Good: "How does the DDS middleware work in ROS 2?"

### Break Down Complex Questions

❌ Bad: "Explain Physical AI, humanoid robotics, sensors, actuators, and control systems"
✅ Good: Ask each topic separately:
- "What is Physical AI?"
- "What sensors are used in humanoid robots?"
- "How do control systems work?"

### Use Selected-Text Mode for Clarity

If you have a specific passage in mind:
1. Highlight it
2. Ask: "Explain this concept"
3. Get a focused answer

## Common Issues

### No Response

**Issue**: You sent a question but nothing happens

**Solutions**:
- Check your internet connection
- Wait a bit longer (can take up to 30 seconds)
- Try refreshing the page
- Check if the backend is running

### Error Message

**Issue**: Red error box appears

**Message**: "Unable to connect to chatbot"

**Solutions**:
- Check internet connection
- Click "Retry" button
- Refresh the page
- Try again later

### Selection Not Detected

**Issue**: You highlighted text but no blue badge appears

**Solutions**:
- Make sure you selected at least 10 characters
- Select plain text (not images or buttons)
- Try selecting again
- Open the chat widget after selecting

### Slow Responses

**Issue**: Answers take a long time

**Normal**: 2-5 seconds is typical
**Long**: 10-30 seconds can happen for complex questions
**Too long**: >30 seconds = timeout (error message appears)

**What to do**:
- Wait patiently
- If timeout occurs, click "Retry"
- Try rephrasing with a simpler question

## Keyboard Shortcuts

### In Chat Input

- **Enter**: Send message
- **Shift + Enter**: New line (multi-line message)
- **Tab**: Navigate between elements
- **Esc**: Close chat panel (keyboard users)

### Accessibility

The chat widget is accessible:

- Screen reader compatible
- Keyboard navigation support
- High contrast mode support
- Focus indicators visible

## Privacy & Data

### What's Stored

**In your browser** (sessionStorage):
- Session ID
- Chat open/close state
- Conversation history (until page refresh)

**On the server**:
- Your questions
- AI answers
- Citations
- Timestamps

### What's NOT Stored

- Personal information
- IP address (not logged)
- Browser fingerprints
- User accounts (no login required)

### Data Usage

- Questions are used to generate answers
- Conversation history improves context understanding
- No data is shared with third parties
- No analytics or tracking

## Examples

### Example 1: Full-Book Question

```
You: What is Physical AI?

AI: Physical AI refers to artificial intelligence systems that
interact with the physical world through sensors and actuators.
Unlike traditional AI that operates purely in the digital realm,
Physical AI must perceive, reason about, and act upon real-world
environments. [Chapter 1, Section 1.1]

Key characteristics:
- Embodiment in physical systems
- Real-time perception and action
- Integration with robotics hardware
- Adaptation to dynamic environments

▼ Sources (2)
  • Chapter 1 - Introduction to Physical AI
    Relevance: 92%
```

### Example 2: Selected-Text Question

```
[You highlight: "DDS is used for inter-node communication"]

📌 Selected: "DDS is used for inter-node communication"

You: What does this mean?

AI: DDS (Data Distribution Service) is a middleware protocol that
enables different nodes (processes or applications) in ROS 2 to
communicate with each other. In the context of this passage, it
means that when different parts of a robot system need to exchange
information, DDS handles the sending and receiving of messages
between them. [Chapter 3, Section 3.2]
```

### Example 3: Follow-up Question

```
You: What sensors are used in humanoid robots?

AI: Humanoid robots typically use several types of sensors:
1. Vision sensors (cameras)
2. Force/torque sensors
3. Inertial Measurement Units (IMUs)
4. Joint encoders
[Chapter 5, Section 5.3]

You: Tell me more about IMUs

AI: IMUs (Inertial Measurement Units) are sensors that measure
acceleration and rotational velocity. In humanoid robots, they're
crucial for balance and orientation sensing... [Chapter 5, Section 5.4]
```

## Getting Help

If you encounter issues:

1. **Try these steps first**:
   - Refresh the page
   - Clear browser cache
   - Try a different question
   - Check your internet connection

2. **Still having trouble?**
   - Check the browser console (F12) for errors
   - Report the issue to the textbook maintainers
   - Include: question asked, error message, browser used

## Best Practices

✅ **Do**:
- Ask clear, specific questions
- Use selected-text mode for focused answers
- Read citations to verify information
- Ask follow-up questions for clarification
- Report bugs or issues

❌ **Don't**:
- Ask questions outside the book's scope
- Expect answers not in the textbook
- Use for homework answers without understanding
- Share sensitive information in questions

## Limitations

The chat assistant:

- **Can answer**: Questions about book content
- **Cannot answer**: Questions outside the book's scope
- **Can explain**: Concepts covered in the textbook
- **Cannot teach**: New material not in the book
- **Can cite**: Sources from the book
- **Cannot reference**: External sources or websites

## Feedback

Help us improve the chat assistant:

- Report incorrect answers
- Suggest better phrasing for refusals
- Request new features
- Share your experience

---

**Version**: 1.0.0
**Last Updated**: 2026-01-03
**Support**: Check the browser console for technical errors
