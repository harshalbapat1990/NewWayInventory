import jsPDF from 'jspdf';
import moment from 'moment';

export function printCustomerSummary(data, customerName, startDate, endDate) {
    // console.log('printCustomerSummary', data, customerName, startDate, endDate);
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    // console.log('pageWidth', pageWidth, 'pageHeight', pageHeight);
    const margin = 8;
    let y = margin;

    // Format dates using moment
    const formattedStartDate = moment(startDate).format('DD MMM YYYY');
    const formattedEndDate = moment(endDate).format('DD MMM YYYY');

    // --- Header ---
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Customer Summary', pageWidth / 2, y, { align: 'center' });
    y += 10;

    const currentDate = moment().format('DD MMM YYYY');
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Generated on:', pageWidth - margin - 50, y); // Adjust position to the right
    doc.setFont('helvetica', 'bold');
    doc.text(currentDate, pageWidth - margin - 25, y); // Adjust position to the right
    y += 6;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Customer:', margin, y);
    doc.setFont('helvetica', 'bold');
    doc.text(customerName, margin + 25, y);
    y += 6;

    doc.setFont('helvetica', 'normal');
    doc.text('Start Date:', margin, y);
    doc.setFont('helvetica', 'bold');
    doc.text(formattedStartDate, margin + 25, y);

    doc.setFont('helvetica', 'normal');
    doc.text('End Date:', pageWidth / 2, y, { align: 'center' });
    doc.setFont('helvetica', 'bold');
    doc.text(formattedEndDate, pageWidth / 2 + 25, y, { align: 'center' });
    y += 10;

    // --- Table Headers ---
    const tableHeaders = ['Size', 'Clr', 'DC', 'Job ID', 'Sets', 'Job Name', 'Remark'];
    const tableXPositions = [margin, 30, 40, 55, 70, 85, pageWidth - margin - 18];

    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    const headerHeight = 6;

    // Draw background rectangle for headers
    doc.setFillColor('#a6a6a6');
    doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');

    // Add header text
    tableHeaders.forEach((header, index) => {
        doc.text(header, tableXPositions[index], y);
    });
    y += headerHeight;

    // --- Table Data ---
    data.forEach((plateGroup) => {
        doc.setFont('helvetica', 'bold');
        doc.text(plateGroup.size, tableXPositions[0], y);
        y += 6;

        plateGroup.colours.forEach((colourGroup) => {
            doc.setFont('helvetica', 'normal');
            doc.text(String(colourGroup.colour), tableXPositions[1] + 2, y);
            y += 6;

            colourGroup.challans.forEach((challanGroup) => {
                doc.text(String(challanGroup.challan_no), tableXPositions[2], y);

                challanGroup.jobs.forEach((job) => {
                    doc.text(String(job.job_id), tableXPositions[3], y);
                    doc.text(String(job.quantity), tableXPositions[4] + 3, y, { align: 'center' });
                    const maxWidth = tableXPositions[6] - tableXPositions[5] - 5; // Calculate available width
                    let jobName = String(job.job_name);
                    if (doc.getTextWidth(jobName) > maxWidth) {
                        while (doc.getTextWidth(jobName + '...') > maxWidth && jobName.length > 0) {
                            jobName = jobName.slice(0, -1); // Trim the string
                        }
                        jobName += '...'; // Add ellipsis
                    }
                    doc.text(jobName, tableXPositions[5], y);
                    const maxRemarkWidth = pageWidth - tableXPositions[6] - margin; // Calculate available width for remark
                    let remark = String(job.remark);
                    if (doc.getTextWidth(remark) > maxRemarkWidth) {
                        while (doc.getTextWidth(remark + '...') > maxRemarkWidth && remark.length > 0) {
                            remark = remark.slice(0, -1); // Trim the string
                        }
                        remark += '...'; // Add ellipsis
                    }
                    doc.text(remark, tableXPositions[6], y);
                    y += 6;

                    // Check if we need a new page
                    if (y + 10 > pageHeight - margin) {
                        doc.addPage();
                        y = margin;

                        // Re-add table headers on new page
                        doc.setFontSize(10);
                        doc.setFont('helvetica', 'bold');
                        doc.setFillColor('#a6a6a6');
                        doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');
                        tableHeaders.forEach((header, index) => {
                            doc.text(header, tableXPositions[index], y);
                        });
                        y += headerHeight;
                    }
                });

                // Add dashed line separator for each challan
                doc.setDrawColor(128);
                doc.setLineWidth(0.1);
                doc.setLineDash([2, 2], 0); // Dashed line
                doc.line(tableXPositions[2], y - 4, pageWidth - margin, y - 4);
            });

            // Add Total Sets for each colour group
            const totalSets = colourGroup.challans.reduce((sum, challanGroup) => {
                return sum + challanGroup.jobs.reduce((jobSum, job) => jobSum + job.quantity, 0);
            }, 0);
            doc.setFont('helvetica', 'bold');
            doc.text('Total Sets:', tableXPositions[2], y);
            doc.text(String(totalSets), tableXPositions[4] + 3, y, { align: 'center' });
            y += 6;

            // Add full line separator after Total Sets for the colour group
            doc.setLineDash([]); // Solid line
            doc.line(margin, y - 4, pageWidth - margin, y - 4);

            // Check if the entire colour group fits on the page
            // console.log(y, y + 36 > pageHeight - margin);
            if (y + 30 > pageHeight - margin) {
                doc.addPage();
                y = margin;

                // Re-add table headers on new page
                doc.setFontSize(10);
                doc.setFont('helvetica', 'bold');
                doc.setFillColor('#a6a6a6');
                doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');
                tableHeaders.forEach((header, index) => {
                    doc.text(header, tableXPositions[index], y);
                });
                y += headerHeight;
            }

        });
        // Add full line separator after Total Sets
        doc.setLineDash([]); // Solid line
        doc.setDrawColor(0, 0, 0); // Set color to full black
        doc.setLineWidth(1); // Set line thickness to 2
        doc.line(margin, y - 4, pageWidth - margin, y - 4);
    });

    // --- Open Print Dialog ---
    doc.autoPrint();
    window.open(doc.output('bloburl'), '_blank');
}

export async function printCustomerSummaryBlob(data, customerName, startDate, endDate) {
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 8;
    let y = margin;

    // Format dates using moment
    const formattedStartDate = moment(startDate).format('DD MMM YYYY');
    const formattedEndDate = moment(endDate).format('DD MMM YYYY');

    // --- Header ---
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Customer Summary', pageWidth / 2, y, { align: 'center' });
    y += 10;

    const currentDate = moment().format('DD MMM YYYY');
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Generated on:', pageWidth - margin - 50, y); // Adjust position to the right
    doc.setFont('helvetica', 'bold');
    doc.text(currentDate, pageWidth - margin - 25, y); // Adjust position to the right
    y += 6;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Customer:', margin, y);
    doc.setFont('helvetica', 'bold');
    doc.text(customerName, margin + 25, y);
    y += 6;

    doc.setFont('helvetica', 'normal');
    doc.text('Start Date:', margin, y);
    doc.setFont('helvetica', 'bold');
    doc.text(formattedStartDate, margin + 25, y);

    doc.setFont('helvetica', 'normal');
    doc.text('End Date:', pageWidth / 2, y, { align: 'center' });
    doc.setFont('helvetica', 'bold');
    doc.text(formattedEndDate, pageWidth / 2 + 25, y, { align: 'center' });
    y += 10;

    // --- Table Headers ---
    const tableHeaders = ['Size', 'Clr', 'DC', 'Job ID', 'Sets', 'Job Name', 'Remark'];
    const tableXPositions = [margin, 30, 40, 55, 70, 85, pageWidth - margin - 18];

    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    const headerHeight = 6;

    // Draw background rectangle for headers
    doc.setFillColor('#a6a6a6');
    doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');

    // Add header text
    tableHeaders.forEach((header, index) => {
        doc.text(header, tableXPositions[index], y);
    });
    y += headerHeight;

    // --- Table Data ---
    data.forEach((plateGroup) => {
        doc.setFont('helvetica', 'bold');
        doc.text(plateGroup.size, tableXPositions[0], y);
        y += 6;

        plateGroup.colours.forEach((colourGroup) => {
            doc.setFont('helvetica', 'normal');
            doc.text(String(colourGroup.colour), tableXPositions[1] + 2, y);
            y += 6;

            colourGroup.challans.forEach((challanGroup) => {
                doc.text(String(challanGroup.challan_no), tableXPositions[2], y);

                challanGroup.jobs.forEach((job) => {
                    doc.text(String(job.job_id), tableXPositions[3], y);
                    doc.text(String(job.quantity), tableXPositions[4] + 3, y, { align: 'center' });
                    const maxWidth = tableXPositions[6] - tableXPositions[5] - 5; // Calculate available width
                    let jobName = String(job.job_name);
                    if (doc.getTextWidth(jobName) > maxWidth) {
                        while (doc.getTextWidth(jobName + '...') > maxWidth && jobName.length > 0) {
                            jobName = jobName.slice(0, -1); // Trim the string
                        }
                        jobName += '...'; // Add ellipsis
                    }
                    doc.text(jobName, tableXPositions[5], y);
                    const maxRemarkWidth = pageWidth - tableXPositions[6] - margin; // Calculate available width for remark
                    let remark = String(job.remark);
                    if (doc.getTextWidth(remark) > maxRemarkWidth) {
                        while (doc.getTextWidth(remark + '...') > maxRemarkWidth && remark.length > 0) {
                            remark = remark.slice(0, -1); // Trim the string
                        }
                        remark += '...'; // Add ellipsis
                    }
                    doc.text(remark, tableXPositions[6], y);
                    y += 6;

                    // Check if we need a new page
                    if (y + 10 > pageHeight - margin) {
                        doc.addPage();
                        y = margin;

                        // Re-add table headers on new page
                        doc.setFontSize(10);
                        doc.setFont('helvetica', 'bold');
                        doc.setFillColor('#a6a6a6');
                        doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');
                        tableHeaders.forEach((header, index) => {
                            doc.text(header, tableXPositions[index], y);
                        });
                        y += headerHeight;
                    }
                });

                // Add dashed line separator for each challan
                doc.setDrawColor(128);
                doc.setLineWidth(0.1);
                doc.setLineDash([2, 2], 0); // Dashed line
                doc.line(tableXPositions[2], y - 4, pageWidth - margin, y - 4);
            });

            // Add Total Sets for each colour group
            const totalSets = colourGroup.challans.reduce((sum, challanGroup) => {
                return sum + challanGroup.jobs.reduce((jobSum, job) => jobSum + job.quantity, 0);
            }, 0);
            doc.setFont('helvetica', 'bold');
            doc.text('Total Sets:', tableXPositions[2], y);
            doc.text(String(totalSets), tableXPositions[4] + 3, y, { align: 'center' });
            y += 6;

            // Add full line separator after Total Sets for the colour group
            doc.setLineDash([]); // Solid line
            doc.line(margin, y - 4, pageWidth - margin, y - 4);

            // Check if the entire colour group fits on the page
            // console.log(y, y + 36 > pageHeight - margin);
            if (y + 30 > pageHeight - margin) {
                doc.addPage();
                y = margin;

                // Re-add table headers on new page
                doc.setFontSize(10);
                doc.setFont('helvetica', 'bold');
                doc.setFillColor('#a6a6a6');
                doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');
                tableHeaders.forEach((header, index) => {
                    doc.text(header, tableXPositions[index], y);
                });
                y += headerHeight;
            }

        });
        // Add full line separator after Total Sets
        doc.setLineDash([]); // Solid line
        doc.setDrawColor(0, 0, 0); // Set color to full black
        doc.setLineWidth(1); // Set line thickness to 2
        doc.line(margin, y - 4, pageWidth - margin, y - 4);
    });

    return doc.output('blob');
}