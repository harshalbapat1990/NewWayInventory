import jsPDF from 'jspdf';
import moment from 'moment';
import axios from '../axios'; // Make sure this import path is correct

export function printChallan(challan, customer, plateSizes) {
  // console.log('Challan:', challan);
  const doc = new jsPDF({
    orientation: 'landscape',
    unit: 'mm',
    format: 'a5',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  // --- Styling Constants ---
  const fontSizeHeader = 14;
  const fontSizeCompany = 11;
  const fontSizeDetailsLabel = 8;
  const fontSizeDetailsValue = 10;
  const fontSizeNote = 10;
  const fontSizeTableHead = 9.5;
  const fontSizeTableBody = 9;
  const fontSizeFooter = 10;
  const fontNormal = 'helvetica';
  const fontBold = 'helvetica';
  const margin = 8;
  const tableXPositions = [margin, 24, 145, 168, 175, 185];

  let y = margin;

  // --- Header ---
  function addHeader() {
    doc.setFontSize(fontSizeHeader);
    doc.setFont(fontBold, 'bold');
    doc.text('DELIVERY CHALLAN', pageWidth / 2, margin, { align: 'center' });
    y = margin + 4;

    // --- Company Details ---
    const companyDetails = {
      name: 'NEW WAY',
      sub: 'TYPESETTERS & PROCESSORS',
      address: [
        'D-102, Sunita Apartment,',
        '1417/18, Kasba Peth, Pune - 411 011.',
      ],
      phone: [
        'Phone: 020-24572977,',
        '+91-9403102988/8446014307',
      ],
    };

    const companyCenterX = pageWidth - (margin + 25);
    doc.setFontSize(18);
    doc.setFont('times', 'bold');
    doc.text(companyDetails.name, companyCenterX, y, { align: 'center' });
    y += 5;
    doc.setFontSize(8);
    doc.text(companyDetails.sub, companyCenterX, y, { align: 'center' });
    y += 5;
    doc.setFontSize(10);
    companyDetails.address.forEach(line => {
      doc.text(line.trim(), companyCenterX, y, { align: 'center' });
      y += 4;
    });
    companyDetails.phone.forEach(line => {
      doc.text(line.trim(), companyCenterX, y, { align: 'center' });
      y += 4;
    });
    y = margin + 10;
  }

  // --- Challan Details ---
  function addChallanDetails() {
    doc.setFontSize(fontSizeDetailsLabel);
    doc.setFont(fontNormal, 'normal');
    doc.text('DC:', margin, y);
    doc.setFontSize(fontSizeDetailsValue);
    doc.setFont(fontBold, 'bold');
    const challanCodeFormatted = challan.challan_code.split('-')[1] || challan.challan_code;
    doc.text(challanCodeFormatted, margin + 8, y);

    doc.setFontSize(fontSizeDetailsLabel);
    doc.text('Date:', pageWidth / 2 - 15, y);
    doc.setFontSize(fontSizeDetailsValue);
    doc.text(moment(challan.date).format('DD MMM YYYY'), pageWidth / 2 - 5, y, { align: 'left' });
    y += 7;

    doc.setFontSize(fontSizeDetailsLabel);
    doc.text('Company:', margin, y);
    doc.setFontSize(14);
    doc.text(customer.company_name || 'N/A', margin + 15, y);
    y += 5;

    doc.setFontSize(fontSizeDetailsLabel);
    doc.text('Contact:', margin, y);
    doc.setFontSize(fontSizeDetailsValue);
    doc.text(customer.contact_person || 'N/A', margin + 15, y);
    y += 5;

    doc.setFontSize(fontSizeDetailsLabel);
    doc.text('Phone:', margin, y);
    doc.setFontSize(fontSizeDetailsValue);
    doc.text(customer.phone || 'N/A', margin + 15, y);

    doc.setFontSize(fontSizeDetailsLabel);
    doc.text('Mobile:', margin + 50, y);
    doc.setFontSize(fontSizeDetailsValue);
    doc.text(customer.mobile || 'N/A', margin + 65, y);
    y += 8;
  }

  // --- Table Headers ---
  function addTableHeaders() {
    doc.setFontSize(fontSizeTableHead);
    doc.setFont(fontNormal, 'bold');
    const tableHeaders = ['Job ID', 'Job Name', 'Size', 'Clr', 'Sets', 'Remark'];
    const headerHeight = 6;

    // Draw background rectangle for headers
    doc.setFillColor('#a6a6a6');
    doc.rect(margin, y - 4, pageWidth - margin * 2, headerHeight, 'F');

    // Add header text
    tableHeaders.forEach((header, index) => {
      doc.text(header, tableXPositions[index], y);
    });
    y += headerHeight;
  }

  // --- Table Data ---
  function addTableData(jobs) {
    jobs.forEach(job => {
      const plateSize = plateSizes.find(
        plate =>
          plate.size_id === job.plate_size_id
      );
      const plateSizeFormatted = plateSize 
        ? `${plateSize.length}x${plateSize.width}${plateSize.is_dl ? '-DL' : ''}` 
        : 'N/A';

      doc.setFontSize(fontSizeTableBody);
      doc.setFont(fontNormal, 'normal');
      doc.text(job.job_id?.toString() || 'N/A', tableXPositions[0], y);
      const maxWidth = tableXPositions[2] - tableXPositions[1] - 2; // Calculate available width
      const jobName = job.job_name || 'N/A';
      const trimmedJobName = doc.getTextWidth(jobName) > maxWidth
        ? doc.splitTextToSize(jobName, maxWidth)[0] + '...'
        : jobName;
      doc.text(trimmedJobName, tableXPositions[1], y);
      doc.text(plateSizeFormatted || 'N/A', tableXPositions[2], y);
      doc.text(job.colour?.toString() || 'N/A', tableXPositions[3] + 2, y, { align: 'center' });
      doc.text(job.quantity?.toString() || 'N/A', tableXPositions[4] + 3, y, { align: 'center' });
      const maxRemarkWidth = pageWidth - tableXPositions[5] - margin; // Calculate available width for remark
      const remark = job.remark?.toString() || '';
      const trimmedRemark = doc.getTextWidth(remark) > maxRemarkWidth
        ? doc.splitTextToSize(remark, maxRemarkWidth)[0] + '...'
        : remark;
      doc.text(trimmedRemark, tableXPositions[5], y);

      // Draw bottom line for the row
      doc.setDrawColor('#bfbfbf');
      doc.line(margin, y + 1, pageWidth - margin, y + 1);

      y += 6; // Move to the next row

      // Check if we need a new page
      if (y + 10 > pageHeight - margin) {
        doc.addPage();
        y = margin;
        addPageHeaderAndFooter();
      }
    });
  }

  // --- Footer ---
  function addFooter() {
    doc.setFontSize(fontSizeFooter);
    doc.text('For New Way', margin, pageHeight - margin);
    
    // Add label for special instructions
    doc.setFontSize(9);
    doc.setFont(fontBold, 'bold');
    doc.text('Special Instructions:', pageWidth / 2, pageHeight - margin - 5, { align: 'center' });

    // Add special instructions at the bottom center if available
    if (challan.special_instructions && challan.special_instructions.trim()) {
      doc.setFontSize(9);
      doc.setFont(fontNormal, 'italic');
      
      // Handle multi-line instructions - limit to 2 lines to fit in footer
      const maxWidth = pageWidth - (margin * 2) - 80; // Leave space for signatures
      const instructionLines = doc.splitTextToSize(challan.special_instructions.trim(), maxWidth);
      // Limit to first two lines if more
      const displayLines = instructionLines.slice(0, 2);
      doc.text(displayLines, pageWidth / 2, pageHeight - margin, { align: 'center' });
    }
    
    doc.setFontSize(fontSizeFooter);
    doc.setFont(fontNormal, 'normal');
    doc.text("Receiver's Signature", pageWidth - margin, pageHeight - margin, { align: 'right' });
  }

  // --- Main Logic ---
  function addPageHeaderAndFooter() {
    addHeader();
    addChallanDetails();
    doc.setFontSize(fontSizeNote);
    doc.setFont(fontBold, 'bold');
    doc.text('Note:', margin, y);
    doc.setFontSize(fontSizeNote);
    doc.setFont(fontNormal, 'normal');
    doc.text('Please receive the undermentioned and return the duplicate duly.', margin + 15, y);
    y += 8;
    
    // Remove special instructions from here as we're moving them to the footer
    addTableHeaders();
  }

  addPageHeaderAndFooter();

  // Split jobs into pages of 12
  const jobsPerPage = 12;
  for (let i = 0; i < challan.jobs.length; i += jobsPerPage) {
    const jobs = challan.jobs.slice(i, i + jobsPerPage);
    addTableData(jobs);

    // Add footer and start a new page if there are more jobs
    if (i + jobsPerPage < challan.jobs.length) {
      addFooter();
      doc.addPage();
      y = margin;
      addPageHeaderAndFooter();
    }
  }

  addFooter();

  // Store the ending page number for the first copy
  const firstCopyPages = doc.internal.getNumberOfPages();
  
  // Add a page for the second copy
  doc.addPage();
  
  // Reset Y position for the second copy
  y = margin;
  
  // Generate second copy
  addPageHeaderAndFooter();
  
  // Split jobs into pages of 12 for the second copy
  for (let i = 0; i < challan.jobs.length; i += jobsPerPage) {
    const jobs = challan.jobs.slice(i, i + jobsPerPage);
    addTableData(jobs);
    
    // Add footer and start a new page if there are more jobs
    if (i + jobsPerPage < challan.jobs.length) {
      addFooter();
      doc.addPage();
      y = margin;
      addPageHeaderAndFooter();
    }
  }
  
  addFooter();

  // --- Open Print Dialog ---
  doc.autoPrint();
  window.open(doc.output('bloburl'), '_blank');
  
  // Mark the challan as printed in the database
  axios.put(`/challans/${challan.id}/mark-printed`)
    .then(() => console.log('Challan marked as printed'))
    .catch(err => console.error('Error marking challan as printed:', err));
  
  // Return the PDF data for potential reuse
  return doc.output('blob');
}