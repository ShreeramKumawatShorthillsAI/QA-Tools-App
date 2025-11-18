"""Report generation for formatting and validation results."""
from datetime import datetime
from typing import Dict, List


class ReportGenerator:
    """Generates formatting and validation reports."""
    
    @staticmethod
    def generate_text_report(report_data: Dict) -> str:
        """
        Generate a formatted text report.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            Formatted report string
        """
        total_issues = sum(len(issues) for issues in report_data['issues_by_model'].values())
        
        report = f"""

# JSON Formatting & Validation Report
**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Summary
- **Total Models Processed:** {report_data['total_models']}
- **Successfully Formatted:** {report_data['processed_models']}
- **Failed Models:** {report_data['failed_models']}
- **Total Issues Fixed:** {total_issues}

---

## Issues Fixed by Model
"""
        
        if report_data['issues_by_model']:
            for model_name, issues in report_data['issues_by_model'].items():
                report += f"\n### 📌 {model_name}\n"
                report += f"**Total Issues:** {len(issues)}\n\n"
                
                for idx, issue in enumerate(issues, 1):
                    clean_issue = issue.split(" in ")[0] if " in " in issue else issue
                    report += f"{idx}. {clean_issue}\n"
                
                report += "\n"
        else:
            report += "\n✅ No issues found - all models are already properly formatted!\n"
        
        report += "\n---\n\n## Errors\n"
        
        if report_data['errors']:
            for error in report_data['errors']:
                report += f"- ❌ {error}\n"
        else:
            report += "\n✅ No errors encountered!\n"
        
        return report
    
    @staticmethod
    def get_summary_stats(report_data: Dict) -> Dict[str, int]:
        """
        Get summary statistics from report.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            Dictionary with summary statistics
        """
        total_issues = sum(len(issues) for issues in report_data['issues_by_model'].values())
        
        return {
            "total_models": report_data['total_models'],
            "processed_models": report_data['processed_models'],
            "failed_models": report_data['failed_models'],
            "total_issues": total_issues
        }

