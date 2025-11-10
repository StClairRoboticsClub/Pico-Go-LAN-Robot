# Director Workflow and Coordination Procedures

## Overview

This document defines the operational procedures for the Director agent, including how it receives tasks, classifies them, delegates to specialized agents, integrates results, and maintains quality standards.

---

## 1. Task Reception

### Input Sources

The Director receives tasks from:
- User/Developer feature requests
- Bug reports
- Performance optimization requests
- Documentation updates
- Architectural improvements
- Integration requirements

### Task Format

All incoming tasks should include:
- **Type**: Feature, Bug, Performance, Documentation, Architecture
- **Priority**: Critical, High, Medium, Low
- **Description**: Clear statement of what needs to be done
- **Context**: Relevant background information
- **Constraints**: Any limitations or requirements
- **Acceptance Criteria**: How success will be measured

### Initial Analysis

Upon receiving a task, Director performs:

1. **Task Classification**
   - Identify task type (feature, bug, performance, etc.)
   - Determine affected components
   - Assess complexity and scope

2. **Dependency Analysis**
   - Identify prerequisite work
   - Map dependencies between components
   - Determine if multi-agent coordination is needed

3. **Resource Assessment**
   - Check file ownership boundaries
   - Identify potential conflicts
   - Assess testing requirements

---

## 2. Task Classification

### Classification Rules

Director classifies tasks using the following decision tree:

#### Step 1: Identify Primary Component
- **Firmware**: Motor control, sensors, watchdog, hardware interfaces
- **Controller**: Input handling, WebSocket, network configuration
- **Documentation**: Guides, performance reports, architecture docs
- **Cross-Agent**: Requires multiple agents

#### Step 2: Determine Complexity
- **Simple**: Single agent, single file/module change
- **Moderate**: Single agent, multiple files, requires testing
- **Complex**: Multiple agents, protocol changes, requires integration

#### Step 3: Check Dependencies
- **Independent**: Can proceed immediately
- **Blocked**: Requires other work first
- **Parallel**: Can work simultaneously with other tasks

### Classification Examples

**Example 1: Simple Firmware Task**
```
Task: "Add dead-zone handling to motor control"
Classification:
  - Primary: Firmware
  - Complexity: Simple
  - Dependencies: None
  - Agent: Firmware Agent
  - Coordination: None required
```

**Example 2: Complex Cross-Agent Task**
```
Task: "Implement new control protocol with encryption"
Classification:
  - Primary: Cross-Agent
  - Complexity: Complex
  - Dependencies: Protocol design first
  - Agents: Firmware + Controller + Documentation
  - Coordination: Director manages integration
```

**Example 3: Performance Task**
```
Task: "Reduce end-to-end latency to <30ms"
Classification:
  - Primary: Cross-Agent
  - Complexity: Moderate
  - Dependencies: Current baseline measurement
  - Agents: Firmware + Controller + Documentation
  - Coordination: Director coordinates optimization
```

---

## 3. Task Routing Logic

### Routing Decision Matrix

| Task Type | Primary Component | Assigned Agent | Coordination Needed |
|-----------|------------------|----------------|-------------------|
| Motor control feature | Firmware | Firmware Agent | None |
| Sensor integration | Firmware | Firmware Agent | None |
| Watchdog improvement | Firmware | Firmware Agent | None |
| Input mapping | Controller | Controller Agent | None |
| WebSocket optimization | Controller | Controller Agent | None |
| Network setup | Controller | Controller Agent | None |
| Documentation update | Documentation | Documentation Agent | None |
| Performance report | Documentation | Documentation Agent | None |
| New protocol | Cross-Agent | Director (coordinates) | Firmware + Controller |
| End-to-end optimization | Cross-Agent | Director (coordinates) | All agents |
| Architecture change | Cross-Agent | Director (coordinates) | All agents |

### Routing Algorithm

```
IF task affects single component AND no protocol changes:
    Route to appropriate specialist agent
    Set coordination: None
    
ELSE IF task affects multiple components:
    Route to Director for coordination
    Identify required agents
    Create subtasks for each agent
    Set coordination: Required
    
ELSE IF task is architectural:
    Route to Director
    Analyze impact on all components
    Create integration plan
    Set coordination: Required
```

---

## 4. Task Delegation

### Delegation Process

#### Step 1: Create Task Specification

For each delegated task, Director provides:

```yaml
Task Specification:
  ID: unique-task-id
  Agent: [firmware|controller|documentation]
  Title: Clear task title
  Description: Detailed description
  Acceptance Criteria:
    - Criterion 1
    - Criterion 2
  Files to Modify:
    - path/to/file1.py
    - path/to/file2.md
  Dependencies:
    - task-id-1 (if any)
  Quality Requirements:
    - Performance: [metric]
    - Code Style: [standard]
    - Testing: [requirements]
  Deadline: [if applicable]
  Priority: [critical|high|medium|low]
```

#### Step 2: Communicate to Agent

Director sends task specification with:
- Clear instructions
- Context and background
- Constraints and limitations
- Expected deliverables
- Integration points (if any)

#### Step 3: Track Progress

Director monitors:
- Task status (in-progress, blocked, complete)
- Progress updates from agent
- Blockers or issues
- Quality checkpoints

### Delegation Examples

**Example: Firmware Task Delegation**
```
To: Firmware Agent
Task: Optimize motor control latency

Specification:
  - Modify: firmware/motor.py
  - Goal: Reduce control latency from 25ms to ≤20ms
  - Test: Measure with oscilloscope and report results
  - Quality: Must maintain PWM stability
  - Deliverables: Updated motor.py, performance report
  
Expected Output:
  - Updated firmware/motor.py
  - Performance metrics (before/after)
  - Testing notes
  - Brief summary of changes
```

**Example: Cross-Agent Task Delegation**
```
To: All Agents (via Director coordination)
Task: Implement new JSON packet structure

Director Plan:
  1. Firmware Agent: Update ws_server.py to handle new format
  2. Controller Agent: Update websocket_client.py to send new format
  3. Documentation Agent: Update protocol documentation
  
Coordination:
  - Director provides packet structure document
  - Agents coordinate through Director for integration
  - Director tests end-to-end compatibility
```

---

## 5. Integration and Merge Procedures

### Integration Workflow

#### Step 1: Receive Completed Work

When an agent completes work, Director receives:
- Updated files with changes
- Commit message describing changes
- Performance metrics (if applicable)
- Testing results
- Brief summary

#### Step 2: Review and Validate

Director performs:

1. **Code Review**
   - Check code style compliance
   - Verify quality standards met
   - Review for architectural consistency
   - Check for potential conflicts

2. **Quality Verification**
   - Validate performance metrics
   - Verify tests pass
   - Check documentation alignment
   - Confirm acceptance criteria met

3. **Conflict Detection**
   - Check for file ownership violations
   - Identify integration conflicts
   - Detect protocol mismatches
   - Find documentation inconsistencies

#### Step 3: Integration Testing

Director runs:
- Unit tests (if applicable)
- Integration tests
- Performance benchmarks
- End-to-end validation
- Compatibility checks

#### Step 4: Merge Decision

Director decides:
- **Approve**: Work meets standards, integrate immediately
- **Request Changes**: Minor issues, agent fixes and resubmits
- **Reject**: Major issues, requires rework
- **Defer**: Blocked by dependencies, wait for other work

### Integration Examples

**Example: Simple Integration**
```
Work Received: Firmware Agent - Motor control optimization
Review:
  ✓ Code style: MicroPython conventions followed
  ✓ Performance: Latency reduced to 18ms (meets ≤20ms requirement)
  ✓ Tests: All hardware tests pass
  ✓ Documentation: Code comments updated
  
Decision: APPROVE
Action: Merge to main, update changelog
```

**Example: Integration with Conflicts**
```
Work Received: Controller Agent - New input mapping
Conflict Detected: Protocol change not coordinated with Firmware

Director Action:
  1. Request Firmware Agent to update protocol handler
  2. Coordinate integration when both complete
  3. Test end-to-end compatibility
  4. Merge both changes together
```

---

## 6. Testing and Validation Checkpoints

### Quality Checkpoints

Director enforces quality at multiple stages:

#### Pre-Delegation Checkpoint
- Task specification complete
- Acceptance criteria clear
- Dependencies identified
- Quality requirements defined

#### Mid-Task Checkpoint (for complex tasks)
- Progress review
- Early issue detection
- Quality validation
- Dependency status

#### Pre-Integration Checkpoint
- Code quality verified
- Performance metrics validated
- Tests passing
- Documentation updated

#### Post-Integration Checkpoint
- Integration tests pass
- System compatibility verified
- Performance maintained/improved
- Documentation accurate

### Validation Procedures

#### Performance Validation
```
For Firmware:
  - Measure control latency (target: ≤20ms)
  - Test fail-safe stop (target: ≤200ms)
  - Verify watchdog timing (target: <200ms)
  
For Controller:
  - Measure network latency (target: <50ms)
  - Test reconnection time (target: <5s)
  - Verify packet delivery (target: >99%)
  
For System:
  - Measure end-to-end latency
  - Test overall reliability
  - Validate user experience
```

#### Code Quality Validation
```
- Code style compliance (PEP8 / MicroPython)
- Variable naming clarity
- Comment quality
- Error handling completeness
- Architecture consistency
```

#### Documentation Validation
```
- Accuracy: Reflects actual implementation
- Completeness: All features documented
- Clarity: New developer can follow
- Reproducibility: Procedures work as written
```

---

## 7. Progress Reporting Format

### Agent Progress Reports

Agents provide progress reports in this format:

```markdown
## Task: [Task ID] - [Task Title]

### Status
[In Progress | Blocked | Complete]

### Progress Summary
[Brief description of work completed]

### Changes Made
- File: path/to/file1.py
  - Change: Description of modification
- File: path/to/file2.md
  - Change: Description of modification

### Performance Metrics
[If applicable]
- Metric 1: Value (target: Target Value)
- Metric 2: Value (target: Target Value)

### Testing Results
[Test results and validation]

### Blockers/Issues
[Any blockers or issues encountered]

### Next Steps
[What remains to be done]
```

### Director Integration Reports

Director provides integration reports:

```markdown
## Integration Report: [Task ID] - [Task Title]

### Agents Involved
- Agent 1: [role]
- Agent 2: [role]

### Work Integrated
[Summary of changes integrated]

### Quality Validation
- Code Quality: [Pass/Fail]
- Performance: [Pass/Fail]
- Testing: [Pass/Fail]
- Documentation: [Pass/Fail]

### Integration Status
[Success | Partial | Failed]

### System Impact
[How this affects the overall system]

### Next Actions
[Any follow-up tasks or coordination needed]
```

---

## 8. Coordination Patterns

### Sequential Coordination

**Use Case**: Tasks with dependencies
```
Task A → Task B → Task C

Director:
  1. Delegate Task A to Agent 1
  2. Wait for Task A completion
  3. Delegate Task B to Agent 2 (depends on A)
  4. Wait for Task B completion
  5. Delegate Task C to Agent 3 (depends on B)
```

### Parallel Coordination

**Use Case**: Independent tasks
```
Task A (Agent 1) ─┐
                  ├─→ Integration
Task B (Agent 2) ─┘

Director:
  1. Delegate Task A and Task B simultaneously
  2. Monitor both in parallel
  3. Integrate when both complete
```

### Hierarchical Coordination

**Use Case**: Complex multi-agent tasks
```
Director
  ├─→ Firmware Agent (Subtask 1)
  ├─→ Controller Agent (Subtask 2)
  └─→ Documentation Agent (Subtask 3)
       └─→ Integration by Director
```

---

## 9. Conflict Resolution

### Conflict Types

1. **File Ownership Conflicts**
   - Agent tries to modify another agent's file
   - Resolution: Director coordinates or reassigns

2. **Protocol Conflicts**
   - Firmware and Controller use incompatible protocols
   - Resolution: Director defines unified protocol, both update

3. **Architecture Conflicts**
   - Changes violate architectural principles
   - Resolution: Director provides architectural guidance

4. **Performance Conflicts**
   - Optimization in one area degrades another
   - Resolution: Director balances trade-offs

### Resolution Process

1. **Identify Conflict**
   - Detect during review or integration
   - Analyze impact and scope

2. **Assess Options**
   - Evaluate alternative approaches
   - Consider trade-offs

3. **Make Decision**
   - Choose resolution approach
   - Communicate to affected agents

4. **Coordinate Resolution**
   - Update task specifications if needed
   - Coordinate agent work
   - Validate resolution

---

## 10. Task Completion

### Completion Criteria

A task is complete when:
- ✅ All acceptance criteria met
- ✅ Quality standards verified
- ✅ Tests passing
- ✅ Documentation updated
- ✅ Integration successful
- ✅ Performance metrics validated

### Completion Process

1. **Final Validation**
   - Director performs final quality check
   - Verifies all criteria met
   - Confirms integration successful

2. **Documentation Update**
   - Update changelog
   - Update relevant documentation
   - Create summary if needed

3. **Communication**
   - Notify user/developer of completion
   - Provide summary of changes
   - Report performance improvements (if any)

4. **Archive**
   - Mark task complete
   - Archive task documentation
   - Update project status

---

## 11. Continuous Improvement

### Process Refinement

Director should:
- Track task completion times
- Monitor quality metrics
- Identify bottlenecks
- Refine routing logic
- Improve coordination patterns

### Feedback Loop

- Collect feedback from agents
- Analyze integration issues
- Update procedures based on learnings
- Refine quality standards
- Improve documentation

---

## 12. Emergency Procedures

### Critical Bug Handling

1. **Immediate Assessment**
   - Evaluate severity and impact
   - Identify affected components

2. **Rapid Delegation**
   - Assign to appropriate agent immediately
   - Set high priority
   - Provide clear fix criteria

3. **Expedited Integration**
   - Fast-track review process
   - Prioritize testing
   - Quick integration if safe

### System Failure Response

1. **Diagnosis**
   - Identify failure point
   - Assess system impact

2. **Recovery Plan**
   - Coordinate with relevant agents
   - Create recovery tasks
   - Prioritize stability

3. **Post-Mortem**
   - Analyze root cause
   - Update procedures
   - Prevent recurrence

---

This workflow ensures systematic, coordinated development while maintaining quality standards and architectural consistency across the Pico-Go LAN Robot project.

