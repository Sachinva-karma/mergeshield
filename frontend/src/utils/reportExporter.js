/**
 * MergeShield Reviewer-Ready Markdown Report Generator
 * Generates an evidence-grounded audit report from live analysis data
 * and triggers a safe browser download.
 */

export function generateMarkdownReport(analysis) {
  if (!analysis || !analysis.pr) {
    throw new Error('Cannot export report: Analysis data is empty or invalid.');
  }

  const { pr, diff_summary, model_info, overall_risk_score, summary_assessment, observed_facts, findings, change_impact } = analysis;
  const timestamp = new Date().toISOString();
  const formattedDate = new Date().toLocaleString();

  // Helper to escape pipe symbols in markdown tables
  const escapeTable = (str) => (str ? String(str).replace(/\|/g, '\\|').replace(/\n/g, ' ') : '');

  let md = `# 🛡️ MergeShield Pull Request Audit Report\n\n`;
  md += `> **Automated Evidence-Backed PR Risk Intelligence & Diff Grounding**  \n`;
  md += `> Generated on: **${formattedDate}** (${timestamp})  \n\n`;

  md += `---\n\n`;

  // 1. Executive Summary & PR Metadata
  md += `## 📋 Pull Request Summary\n\n`;
  md += `| Property | Details |\n`;
  md += `| :--- | :--- |\n`;
  md += `| **Repository** | [${pr.owner}/${pr.repo}](https://github.com/${pr.owner}/${pr.repo}) |\n`;
  md += `| **Pull Request** | [#${pr.pr_number}: ${escapeTable(pr.title)}](${pr.html_url}) |\n`;
  md += `| **Author** | [@${pr.author}](https://github.com/${pr.author}) |\n`;
  md += `| **Branch Target** | \`${pr.base_branch}\` &larr; \`${pr.head_branch}\` |\n`;
  md += `| **Diff Metrics** | ${pr.changed_files_count} files modified (+${pr.additions} / -${pr.deletions}) |\n`;
  md += `| **Overall Risk Score** | **${overall_risk_score}** |\n`;
  md += `| **Foundation Model** | \`${model_info?.model_name || 'qwen/qwen3.8-27b'}\` (${model_info?.model_license || 'Apache 2.0 Open Weights'}) |\n`;
  md += `| **Analysis Engine** | Hosted via ${model_info?.provider || 'Groq Cloud'} (Grounding Enforced) |\n\n`;

  md += `### Executive Assessment\n\n`;
  md += `> ${summary_assessment}\n\n`;

  // 2. Observed Facts
  if (observed_facts && observed_facts.length > 0) {
    md += `### Observed Facts (Retrieved Context)\n\n`;
    observed_facts.forEach((fact) => {
      md += `- ${fact}\n`;
    });
    md += `\n`;
  }

  // 3. Change Impact Map Summary
  if (change_impact) {
    md += `## 🗺️ Change Impact Map\n\n`;
    md += `**Test Verification Signal:** ${change_impact.test_coverage_signal}\n\n`;

    if (change_impact.has_missing_tests_signal) {
      md += `> ⚠️ **Review Signal**: Application logic or contracts were modified with no test file updates in this pull request. Reviewers should investigate whether existing coverage is sufficient.\n\n`;
    }

    if (change_impact.category_counts && Object.keys(change_impact.category_counts).length > 0) {
      md += `### Category Breakdown\n\n`;
      md += `| Category | Files Analyzed |\n`;
      md += `| :--- | :---: |\n`;
      Object.entries(change_impact.category_counts).forEach(([cat, count]) => {
        md += `| ${cat} | ${count} |\n`;
      });
      md += `\n`;
    }

    if (change_impact.files && change_impact.files.length > 0) {
      md += `### Modified Files & Grounded Interface Shifts\n\n`;
      change_impact.files.forEach((f) => {
        md += `#### \`${f.file_path}\`\n`;
        md += `- **Status:** \`${f.status.toUpperCase()}\` | **Category:** ${f.category} | **Lines:** +${f.additions} / -${f.deletions}\n`;
        if (f.associated_finding_ids && f.associated_finding_ids.length > 0) {
          md += `- **Associated Findings:** ${f.associated_finding_ids.join(', ')}\n`;
        }

        if (f.detected_interfaces && f.detected_interfaces.length > 0) {
          md += `- **Directly Visible Interface Changes:**\n`;
          f.detected_interfaces.forEach((iface) => {
            md += `  - \`${iface.change_type}\`: \`${iface.name}\`${iface.line_number ? ` (Line ${iface.line_number})` : ''} — ${iface.details || ''}\n`;
          });
        }

        if (f.potential_downstream_impacts && f.potential_downstream_impacts.length > 0) {
          md += `- **Potential Downstream Consequences (Inferred):**\n`;
          f.potential_downstream_impacts.forEach((imp) => {
            md += `  - ${imp}\n`;
          });
        }
        md += `\n`;
      });
    }

    md += `*Context Limitation: ${change_impact.context_limitation_note}*\n\n`;
  }

  // 4. Prioritized Key Findings
  md += `## 🔍 Key Review Findings (${findings ? findings.length : 0})\n\n`;

  if (!findings || findings.length === 0) {
    md += `✅ **No high-risk security flaws or regression patterns identified in the analyzed diff.**\n\n`;
  } else {
    findings.forEach((finding, idx) => {
      const priorityLabel = finding.priority || 'Normal';
      const evidenceStrength = finding.evidence_strength || 'Verified in Diff';

      md += `### ${idx + 1}. [${finding.id}] ${finding.summary}\n\n`;
      md += `| Attribute | Classification |\n`;
      md += `| :--- | :--- |\n`;
      md += `| **Priority** | **${priorityLabel}** |\n`;
      md += `| **Severity** | **${finding.severity}** |\n`;
      md += `| **Evidence Strength** | **${evidenceStrength}** |\n`;
      md += `| **Category** | ${finding.category} |\n\n`;

      if (finding.priority_reasoning) {
        md += `**Why Investigate This First:** ${finding.priority_reasoning}\n\n`;
      }

      md += `**Explanation:**\n${finding.explanation}\n\n`;

      if (finding.uncertainty) {
        md += `> ℹ️ **Context Uncertainty:** ${finding.uncertainty}\n\n`;
      }

      // Supporting Diff Evidence
      if (finding.evidence && finding.evidence.length > 0) {
        md += `#### Supporting Diff Evidence\n\n`;
        finding.evidence.forEach((ev) => {
          const lineRef = ev.line_start ? ` (Lines L${ev.line_start}${ev.line_end ? `-L${ev.line_end}` : ''})` : '';
          const lineType = ev.is_changed_line ? 'Modified Line (+/-)' : 'Surrounding Context ( )';
          const verifiedBadge = ev.is_verified_in_diff ? '✅ Verified in Diff' : '⚠️ Unverified Caveat';

          md += `- **File:** \`${ev.file_path}\`${lineRef} — *${lineType}* [${verifiedBadge}]\n`;
          md += `\`\`\`\n${ev.snippet}\n\`\`\`\n\n`;
        });
      }

      // Smart Verification Actions
      if (finding.verification_plan && finding.verification_plan.length > 0) {
        md += `#### Actionable Verification Plan\n\n`;
        finding.verification_plan.forEach((action, aIdx) => {
          md += `**Action ${aIdx + 1} (${action.action_type}):**\n`;
          md += `- **What to verify:** ${action.what_to_verify}\n`;
          md += `- **Why it matters:** ${action.why_it_matters}\n`;
          md += `- **Expected behavior:** ${action.expected_behavior}\n`;
          if (action.suggested_scenario) {
            md += `- **Suggested test scenario:** \`${action.suggested_scenario}\`\n`;
          }
          md += `- **Execution status:** \`Suggested for Developer Verification (Not Executed by Auditor)\`\n\n`;
        });
      } else if (finding.suggested_tests && finding.suggested_tests.length > 0) {
        md += `#### Recommended Verification Tests\n\n`;
        finding.suggested_tests.forEach((t) => {
          md += `- ${t} *(Status: Suggested only; not executed)*\n`;
        });
        md += `\n`;
      }

      md += `---\n\n`;
    });
  }

  // 5. Verification Checklist
  if (findings && findings.length > 0) {
    md += `## ✅ Comprehensive Reviewer Verification Checklist\n\n`;
    findings.forEach((finding) => {
      const tests = finding.verification_plan && finding.verification_plan.length > 0
        ? finding.verification_plan.map(v => v.what_to_verify)
        : finding.suggested_tests || [];

      tests.forEach((t) => {
        md += `- [ ] **[${finding.id}]** ${t}\n`;
      });
    });
    md += `\n---\n\n`;
  }

  // 6. Explicit Boundaries & Limitations
  md += `## ⚖️ Limitations & Disclosures\n\n`;
  md += `1. **Static Reasoning Only:** MergeShield performs static heuristic and open-weight model analysis on unified diffs. It does not execute repository code, install dependencies, or execute runtime test suites.\n`;
  md += `2. **Context Bounding:** The analyzed diff is bounded to ${diff_summary?.total_lines || 1500} lines to preserve deterministic model latency. Callers, imported modules, and runtime side-effects outside the pull request were not inspected.\n`;
  md += `3. **Grounding Verification:** Verbatim code excerpts are checked against the retrieved diff. Any ungrounded snippets are marked with explicit unverified caveats.\n`;
  md += `4. **Responsible Disclosure:** This report is an assistive developer intelligence artifact, not a formal security certification or penetration test report.\n\n`;

  md += `---\n`;
  md += `*Report generated by [MergeShield](https://github.com/${pr.owner}/${pr.repo}) • Open Weights powered by Apache 2.0 Licensed Models • MIT License*\n`;

  return md;
}

export function downloadMarkdownReport(analysis) {
  const markdownContent = generateMarkdownReport(analysis);
  const pr = analysis.pr;
  const fileName = `mergeshield-report-${pr.owner}-${pr.repo}-pr${pr.pr_number}.md`;

  const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
