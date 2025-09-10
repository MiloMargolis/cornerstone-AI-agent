# TODO: AI Agent Conversation Improvements

## Completed ✅
- **Solution 1**: Fixed race condition in lead processing by refreshing lead object after database update
- **Solution 4**: Fixed phase logic to account for what was just extracted in current message

## Pending Implementation 🔄

### Solution 2: Implement Conversation State Management
**Problem**: Each message is processed independently without proper state tracking.

**Implementation Plan**:
- Create `ConversationState` class in `src/core/conversation_state.py`
- Track what was just extracted in current message
- Track questions asked in current session
- Track multi-question flow state
- Pass state between extraction and response generation

**Files to modify**:
- `src/core/conversation_state.py` (new)
- `src/core/lead_processor.py`
- `src/services/ai/openai_service.py`

### Solution 3: Enhance Chat History Management
**Problem**: Only last 10 messages are kept, losing important context.

**Implementation Plan**:
- Implement conversation summary that captures key decisions and extracted info
- Use summary + recent messages instead of just truncating
- Add session context tracking current conversation flow
- Store conversation summaries in database

**Files to modify**:
- `src/models/lead.py` (add conversation_summary field)
- `src/services/database/lead_repository.py`
- `src/services/ai/openai_service.py`
- `src/utils/prompts/` (add summary generation prompt)

### Solution 5: Implement Immediate Context Awareness
**Problem**: AI doesn't "see" what was just extracted when generating responses.

**Implementation Plan**:
- Pass extracted_info directly to generate_response()
- Modify prompt to include "JUST EXTRACTED" information section
- Update database status to reflect both stored data AND current extraction
- Add immediate context to AI prompts

**Files to modify**:
- `src/utils/prompts/qualification_system.tmpl`
- `src/services/ai/openai_service.py`

### Solution 6: Add Conversation Flow Tracking
**Problem**: No tracking of what questions were asked in current session.

**Implementation Plan**:
- Add `session_questions_asked` field to Lead model
- Clear when starting new session or after delay
- Use to avoid repeating questions within same conversation
- Track question-answer pairs in session

**Files to modify**:
- `src/models/lead.py`
- `src/services/database/lead_repository.py`
- `src/core/lead_processor.py`

## Additional Improvements

### Solution 7: Smart Question Bundling
**Problem**: AI asks questions inefficiently without considering conversation flow.

**Implementation Plan**:
- Implement question prioritization based on lead urgency
- Bundle related questions together
- Avoid asking about fields that are likely to be provided together
- Use conversation context to predict what lead might provide next

### Solution 8: Conversation Session Management
**Problem**: No clear session boundaries or conversation resets.

**Implementation Plan**:
- Define session boundaries (time gaps, new topics)
- Implement conversation reset logic
- Track session start/end times
- Clear session-specific state appropriately

### Solution 9: Enhanced Error Recovery
**Problem**: When extraction fails, AI doesn't handle gracefully.

**Implementation Plan**:
- Implement fallback extraction strategies
- Add conversation recovery mechanisms
- Handle partial information gracefully
- Provide better error messages to users

## Priority Order
1. **Solution 2** (Conversation State Management) - High impact, moderate complexity
2. **Solution 5** (Immediate Context Awareness) - High impact, low complexity  
3. **Solution 3** (Chat History Management) - Medium impact, high complexity
4. **Solution 6** (Conversation Flow Tracking) - Medium impact, moderate complexity
5. **Solution 7** (Smart Question Bundling) - Low impact, high complexity
6. **Solution 8** (Session Management) - Low impact, moderate complexity
7. **Solution 9** (Error Recovery) - Medium impact, low complexity

## Testing Strategy
- Unit tests for each new component
- Integration tests for conversation flows
- End-to-end tests with realistic conversation scenarios
- Performance tests for chat history management
- Regression tests to ensure existing functionality works
