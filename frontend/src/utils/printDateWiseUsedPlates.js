import jsPDF from 'jspdf';
import moment from 'moment';

export function printDateWiseUsedPlates(data, startDate, endDate) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a5',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  const margin = 10;
  let y = margin;

  // Format dates using moment
  const formattedStartDate = moment(startDate).format('DD MMM YYYY');
  const formattedEndDate = moment(endDate).format('DD MMM YYYY');

  // --- Header ---
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('Date Wise Used Plates', pageWidth / 2, y, { align: 'center' });
  y += 10;

  const currentDate = moment().format('DD MMM YYYY');
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text('Generated on:', pageWidth - margin - 25, y, { align: 'right' }); // Adjust position to the right
  doc.setFont('helvetica', 'bold');
  doc.text(currentDate, pageWidth - margin, y, { align: 'right' }); // Adjust position to the right
  y += 10;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text('Start Date:', margin, y);
  doc.setFont('helvetica', 'bold');
  doc.text(formattedStartDate, margin + 20, y);
  doc.setFont('helvetica', 'normal');

  doc.text('End Date:', pageWidth - margin - 25, y, { align: 'right' });
  doc.setFont('helvetica', 'bold');
  doc.text(formattedEndDate, pageWidth - margin, y, { align: 'right' });
  doc.setFont('helvetica', 'normal');
  y += 10;

  // --- Table Headers ---
  const tableHeaders = ['Plate Size', 'Quantity'];
  const tableXPositions = [margin, pageWidth - 50];

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
  data.forEach((row) => {
    doc.setFont('helvetica', 'normal');
    doc.text(row.item, tableXPositions[0], y);
    doc.text(row.quantity.toString(), tableXPositions[1], y);

    // Draw bottom line for the row
    doc.setDrawColor('#bfbfbf');
    doc.line(margin, y + 1, pageWidth - margin, y + 1);

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


  // --- Open Print Dialog ---
  doc.autoPrint();
  window.open(doc.output('bloburl'), '_blank');
}