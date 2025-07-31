import jsPDF from 'jspdf';
import 'jspdf-autotable';

// Extend jsPDF type to include autoTable
declare module 'jspdf' {
    interface jsPDF {
        autoTable: (options: any) => jsPDF;
        lastAutoTable?: {
            finalY: number;
        };
    }
}

export const generateAgentSpecPDF = (spec: any) => {
    const doc = new jsPDF();
    let yPosition = 20;

    // Add logo - using text for now, but you can add an actual image
    doc.setFontSize(24);
    doc.setTextColor(0, 0, 0); // Black
    doc.text('nBrain', 20, yPosition);
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text('AI Development Company', 20, yPosition + 8);
    
    // Add horizontal line
    yPosition += 15;
    doc.setDrawColor(0, 0, 0); // Black line
    doc.line(20, yPosition, 190, yPosition);
    
    // Title
    yPosition += 15;
    doc.setFontSize(20);
    doc.setTextColor(0);
    doc.text(spec.title || 'Agent Specification', 20, yPosition);
    
    // Date and Type
    yPosition += 10;
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Type: ${spec.agent_type?.replace('_', ' ').toUpperCase() || 'CUSTOM'}`, 20, yPosition);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, 150, yPosition);
    
    // Summary
    yPosition += 15;
    doc.setFontSize(12);
    doc.setTextColor(0);
    doc.setFont('helvetica', 'bold');
    doc.text('Executive Summary', 20, yPosition);
    doc.setFont('helvetica', 'normal');
    yPosition += 8;
    doc.setFontSize(10);
    const summaryLines = doc.splitTextToSize(spec.summary || '', 170);
    doc.text(summaryLines, 20, yPosition);
    yPosition += summaryLines.length * 5 + 10;

    // Value Proposition
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text('Value Proposition:', 20, yPosition);
    doc.setFont('helvetica', 'normal');
    yPosition += 8;
    doc.setFontSize(10);
    const valueProposition = `This AI agent will transform your ${spec.agent_type?.replace('_', ' ')} operations by automating key processes, reducing operational costs by up to 90%, and improving response times from hours to seconds. By leveraging cutting-edge AI technology, your team will be freed from repetitive tasks to focus on high-value strategic initiatives.`;
    const valuePropLines = doc.splitTextToSize(valueProposition, 170);
    doc.text(valuePropLines, 20, yPosition);
    yPosition += valuePropLines.length * 5 + 15;

    // Check if we need a new page
    if (yPosition > 240) {
        doc.addPage();
        yPosition = 20;
    }

    // Business Case & ROI
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Business Case & ROI', 20, yPosition);
    yPosition += 10;

    const businessCaseData = [
        ['Current State Challenges', 'Future State Benefits'],
        ['• Manual processes consuming valuable human resources\n• Inconsistent quality and response times\n• Limited scalability with growing demands\n• High operational costs and error rates', 
         '• 24/7 automated operations with consistent quality\n• Instant response times and infinite scalability\n• 90% reduction in operational costs\n• Data-driven insights for continuous improvement']
    ];

    doc.autoTable({
        startY: yPosition,
        head: [businessCaseData[0]],
        body: [businessCaseData[1]],
        theme: 'grid',
        headStyles: { 
            fillColor: [0, 0, 0],
            textColor: 255 
        },
        columnStyles: {
            0: { cellWidth: 85 },
            1: { cellWidth: 85 }
        },
        styles: {
            cellPadding: 5,
            fontSize: 9,
            lineColor: [0, 0, 0],
            lineWidth: 0.1
        }
    });

    yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;

    // Success Metrics
    if (yPosition > 200) {
        doc.addPage();
        yPosition = 20;
    }

    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Success Metrics & KPIs', 20, yPosition);
    yPosition += 10;

    const metricsData = [
        ['Metric', 'Target', 'Description'],
        ['Efficiency Gains', '90%', 'Reduction in processing time'],
        ['Cost Savings', '85%', 'Lower operational costs'],
        ['Quality Improvement', '99%', 'Consistency in outputs']
    ];

    doc.autoTable({
        startY: yPosition,
        head: [metricsData[0]],
        body: metricsData.slice(1),
        theme: 'grid',
        headStyles: { 
            fillColor: [0, 0, 0],
            textColor: 255 
        },
        columnStyles: {
            0: { cellWidth: 60 },
            1: { cellWidth: 30, halign: 'center' },
            2: { cellWidth: 80 }
        },
        styles: {
            fontSize: 10
        }
    });

    yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;

    // Risk Mitigation Strategy
    if (yPosition > 200) {
        doc.addPage();
        yPosition = 20;
    }

    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Risk Mitigation Strategy', 20, yPosition);
    yPosition += 10;

    const riskData = [
        ['Risk Level', 'Area', 'Mitigation Strategy'],
        ['Medium', 'Data Privacy & Security', 'Implement end-to-end encryption, role-based access control, and regular security audits'],
        ['Low', 'User Adoption', 'Comprehensive training program, intuitive UI design, and phased rollout approach'],
        ['Minimal', 'Technical Integration', 'Use of industry-standard APIs, extensive testing, and fallback mechanisms']
    ];

    doc.autoTable({
        startY: yPosition,
        head: [riskData[0]],
        body: riskData.slice(1),
        theme: 'grid',
        headStyles: { 
            fillColor: [0, 0, 0],
            textColor: 255 
        },
        columnStyles: {
            0: { cellWidth: 25 },
            1: { cellWidth: 45 },
            2: { cellWidth: 100 }
        },
        styles: {
            fontSize: 9
        }
    });

    yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;

    // Check if we need a new page
    if (yPosition > 200) {
        doc.addPage();
        yPosition = 20;
    }

    // Implementation Steps - Detailed
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Detailed Implementation Plan', 20, yPosition);
    doc.setFont('helvetica', 'normal');
    yPosition += 10;

    const stepsData = spec.steps?.map((step: string, index: number) => {
        const parts = step.split(':');
        const stepTitle = parts[0] || step;
        const stepDetail = parts.slice(1).join(':').trim() || step;
        
        const deliverables = step.toLowerCase().includes('api') ? 'API endpoints' : 
                           step.toLowerCase().includes('test') ? 'Test reports and quality assurance documentation' :
                           step.toLowerCase().includes('deploy') ? 'Production-ready deployment with monitoring' :
                           'Implementation artifacts and documentation';
        
        return [
            `${index + 1}`,
            stepTitle,
            stepDetail,
            deliverables
        ];
    }) || [];

    doc.autoTable({
        startY: yPosition,
        head: [['#', 'Phase', 'Description', 'Deliverables']],
        body: stepsData,
        theme: 'grid',
        headStyles: { 
            fillColor: [0, 0, 0], // Black header
            textColor: 255 
        },
        alternateRowStyles: {
            fillColor: [245, 245, 245] // Light gray for alternate rows
        },
        columnStyles: {
            0: { cellWidth: 20 },
            1: { cellWidth: 40 },
            2: { cellWidth: 70 },
            3: { cellWidth: 40 }
        },
        styles: {
            fontSize: 9,
            cellPadding: 3
        }
    });

    yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;

    // Technical Stack
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Technical Stack', 20, yPosition);
    yPosition += 10;

    const stackData: any[] = [];
    Object.entries(spec.agent_stack || {}).forEach(([key, value]) => {
        const componentName = key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.replace(/_/g, ' ').slice(1);
        
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            // Handle nested objects (like llm_model, vector_database, etc.)
            Object.entries(value).forEach(([subKey, subValue]) => {
                const subComponentName = `${componentName} - ${subKey.replace(/_/g, ' ').charAt(0).toUpperCase() + subKey.replace(/_/g, ' ').slice(1)}`;
                stackData.push([
                    subComponentName,
                    Array.isArray(subValue) ? subValue.join(', ') : String(subValue || 'Not specified')
                ]);
            });
        } else {
            stackData.push([
                componentName,
                Array.isArray(value) ? value.join(', ') : String(value || 'Not specified')
            ]);
        }
    });

    doc.autoTable({
        startY: yPosition,
        head: [['Component', 'Technology/Details']],
        body: stackData,
        theme: 'grid',
        headStyles: { 
            fillColor: [0, 0, 0], // Black header
            textColor: 255 
        },
        alternateRowStyles: {
            fillColor: [245, 245, 245] // Light gray for alternate rows
        },
        columnStyles: {
            0: { cellWidth: 70 },
            1: { cellWidth: 100 }
        },
        styles: {
            fontSize: 9
        }
    });

    yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;

    // Security Considerations
    if (spec.security_considerations) {
        if (yPosition > 200) {
            doc.addPage();
            yPosition = 20;
        }

        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Security Considerations', 20, yPosition);
        yPosition += 10;

        const securityData: any[] = [];
        Object.entries(spec.security_considerations).forEach(([category, details]) => {
            const categoryName = category.replace(/_/g, ' ').charAt(0).toUpperCase() + category.replace(/_/g, ' ').slice(1);
            
            if (typeof details === 'object' && details !== null) {
                Object.entries(details).forEach(([key, value]) => {
                    const keyName = key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.replace(/_/g, ' ').slice(1);
                    securityData.push([
                        categoryName,
                        keyName,
                        Array.isArray(value) ? value.join(', ') : String(value || 'Not specified')
                    ]);
                });
            } else {
                securityData.push([categoryName, '', String(details)]);
            }
        });

        doc.autoTable({
            startY: yPosition,
            head: [['Category', 'Aspect', 'Implementation']],
            body: securityData,
            theme: 'grid',
            headStyles: { 
                fillColor: [0, 0, 0],
                textColor: 255 
            },
            alternateRowStyles: {
                fillColor: [245, 245, 245]
            },
            columnStyles: {
                0: { cellWidth: 45 },
                1: { cellWidth: 45 },
                2: { cellWidth: 80 }
            },
            styles: {
                fontSize: 9
            }
        });

        yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;
    }

    // Check if we need a new page
    if (yPosition > 250) {
        doc.addPage();
        yPosition = 20;
    }

    // Client Requirements
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Client Requirements', 20, yPosition);
    yPosition += 10;

    const reqData = spec.client_requirements?.map((req: string, index: number) => [
        `${index + 1}`,
        req
    ]) || [];

    doc.autoTable({
        startY: yPosition,
        head: [['#', 'Requirement']],
        body: reqData,
        theme: 'grid',
        headStyles: { 
            fillColor: [0, 0, 0], // Black header
            textColor: 255 
        },
        alternateRowStyles: {
            fillColor: [245, 245, 245] // Light gray for alternate rows
        },
        columnStyles: {
            0: { cellWidth: 20 },
            1: { cellWidth: 150 }
        }
    });

    // Future Enhancements
    if (spec.future_enhancements && spec.future_enhancements.length > 0) {
        if (yPosition > 200) {
            doc.addPage();
            yPosition = 20;
        }

        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Future Enhancement Opportunities', 20, yPosition);
        yPosition += 10;

        const enhancementData = spec.future_enhancements.map((enhancement: any, index: number) => {
            if (typeof enhancement === 'object') {
                return [
                    `${index + 1}`,
                    enhancement.enhancement || 'Enhancement',
                    enhancement.description || '',
                    enhancement.impact || '',
                    enhancement.implementation_effort || 'TBD'
                ];
            } else {
                return [`${index + 1}`, String(enhancement), '', '', 'TBD'];
            }
        });

        doc.autoTable({
            startY: yPosition,
            head: [['#', 'Enhancement', 'Description', 'Business Impact', 'Effort']],
            body: enhancementData,
            theme: 'grid',
            headStyles: { 
                fillColor: [0, 0, 0],
                textColor: 255 
            },
            alternateRowStyles: {
                fillColor: [245, 245, 245]
            },
            columnStyles: {
                0: { cellWidth: 10 },
                1: { cellWidth: 35 },
                2: { cellWidth: 65 },
                3: { cellWidth: 40 },
                4: { cellWidth: 20 }
            },
            styles: {
                fontSize: 8,
                cellPadding: 2
            }
        });

        yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;
    }

    // Cost Estimate (if available)
    if (spec.implementation_estimate) {
        yPosition = (doc.lastAutoTable?.finalY || yPosition) + 15;
        
        if (yPosition > 200) {
            doc.addPage();
            yPosition = 20;
        }

        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Cost Estimate', 20, yPosition);
        yPosition += 10;

        const costData = [
            ['Approach', 'Hours', 'Cost'],
            [
                'Traditional Development',
                spec.implementation_estimate.traditional_approach?.hours || 'N/A',
                spec.implementation_estimate.traditional_approach?.total_cost || 'N/A'
            ],
            [
                'AI-Powered (nBrain)',
                spec.implementation_estimate.ai_powered_approach?.hours || 'N/A',
                spec.implementation_estimate.ai_powered_approach?.total_cost || 'N/A'
            ]
        ];

        doc.autoTable({
            startY: yPosition,
            body: costData,
            theme: 'grid',
            headStyles: { 
                fillColor: [0, 0, 0], // Black header
                textColor: 255 
            },
            didParseCell: function(data: any) {
                if (data.row.index === 0) {
                    data.cell.styles.fillColor = [0, 0, 0];
                    data.cell.styles.textColor = 255;
                    data.cell.styles.fontStyle = 'bold';
                }
                if (data.row.index === 2) {
                    data.cell.styles.fillColor = [230, 230, 230]; // Light gray for AI-powered row
                    data.cell.styles.fontStyle = 'bold';
                }
            }
        });

        // Add savings note
        yPosition = (doc.lastAutoTable?.finalY || yPosition) + 5;
        doc.setFontSize(10);
        doc.setTextColor(0, 0, 0);
        doc.setFont('helvetica', 'bold');
        doc.text('* 90% cost savings with AI-powered development', 20, yPosition);
    }

    // Footer
    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(
            `Page ${i} of ${pageCount} | Generated by nBrain Agent Ideator`,
            105,
            290,
            { align: 'center' }
        );
    }

    // Save the PDF
    doc.save(`${spec.title?.replace(/\s+/g, '_') || 'agent_specification'}.pdf`);
}; 