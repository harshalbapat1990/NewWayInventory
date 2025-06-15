import jsPDF from 'jspdf';
import moment from 'moment';
import newWayLogo from '../assets/NewWayLogo.png';

export function printTaxInvoice(invoiceData, customerData, itemsData, ratesData, shouldPrint = true) {
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
    });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const fontSizeHeader = 16;
    const fontSizeCompany = 12;
    const fontSizeDetailsLabel = 9;
    const fontSizeDetailsValue = 10;
    const fontSizeTableHead = 10;
    const fontSizeTableBody = 9;
    const fontSizeFooter = 10;
    const fontNormal = 'helvetica';
    const fontBold = 'helvetica';
    const margin = 10;
    const tableMargin = margin;
    let y = margin;

    const tableXPositions = [
        tableMargin,
        tableMargin + 8,
        tableMargin + 117,
        tableMargin + 135,
        tableMargin + 145,
        tableMargin + 160,
        tableMargin + 170,
        pageWidth - tableMargin
    ];

    function addHeader() {
        doc.setFontSize(fontSizeHeader);
        doc.setFont(fontBold, 'bold');
        doc.text('TAX INVOICE', pageWidth / 2, y, { align: 'center' });
        y += 4;

        const colWidth = (pageWidth - margin * 2) / 2;
        const leftColX = margin;
        const rightColX = margin + colWidth;
        const boxHeight = 50;
        const startY = y;

        doc.setDrawColor(0);
        doc.setLineWidth(0.5);
        doc.rect(leftColX, startY, colWidth, boxHeight);
        doc.rect(rightColX, startY, colWidth, boxHeight);

        let customerY = startY + 5;
        doc.setFontSize(10);
        doc.setFont(fontBold, 'bold');
        doc.text('Buyer (Bill to):', leftColX + 5, customerY);
        customerY += 6;

        doc.setFontSize(9);
        doc.setFont(fontNormal, 'bold');
        doc.text(`${customerData.company_name || 'N/A'}`, leftColX + 5, customerY);
        customerY += 4;

        doc.setFontSize(8);
        doc.setFont(fontNormal, 'normal');
        const addressLines = doc.splitTextToSize(customerData.address || 'N/A', colWidth - 10);
        addressLines.forEach(line => {
            doc.text(line, leftColX + 5, customerY);
            customerY += 4;
        });

        doc.text(`GSTIN: ${customerData.gstin || 'N/A'}`, leftColX + 5, customerY);
        customerY += 4;

        if (customerData.state) {
            doc.text(`State: ${customerData.state || 'Maharashtra'}, Code: ${customerData.code || '27'}`, leftColX + 5, customerY);
            customerY += 4;
        }

        doc.text(`Contact: ${customerData.contact_person || 'N/A'}`, leftColX + 5, customerY);
        customerY += 4;

        doc.text(`Phone: ${customerData.phone || 'N/A'}`, leftColX + 5, customerY);
        customerY += 4;

        doc.text(`Mobile: ${customerData.mobile || 'N/A'}`, leftColX + 5, customerY);
        customerY += 4;

        doc.text(`Email: ${customerData.email || 'N/A'}`, leftColX + 5, customerY);

        let companyY = startY + 5;
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
            gst: 'GSTIN: 27AAAFN9711H1Z9',
            state: 'State: Maharashtra, Code: 27',
            email: 'E-Mail: newwayaccounts@gmail.com'
        };

        doc.setFontSize(10);
        doc.setFont('times', 'bold');
        doc.text(companyDetails.name, rightColX + 5, companyY);
        companyY += 5;

        doc.setFontSize(8);
        doc.text(companyDetails.sub, rightColX + 5, companyY);
        companyY += 5;

        doc.setFontSize(8);
        doc.setFont(fontNormal, 'normal');
        companyDetails.address.forEach(line => {
            doc.text(line.trim(), rightColX + 5, companyY);
            companyY += 4;
        });

        companyDetails.phone.forEach(line => {
            doc.text(line.trim(), rightColX + 5, companyY);
            companyY += 4;
        });

        doc.text(companyDetails.gst, rightColX + 5, companyY);
        companyY += 4;

        doc.text(companyDetails.state, rightColX + 5, companyY);
        companyY += 4;

        doc.text(companyDetails.email, rightColX + 5, companyY);

        y = startY + boxHeight;
    }

    function addInvoiceDetails() {
        const boxWidth = pageWidth - margin * 2;
        const boxHeight = 6;

        doc.setDrawColor(0);
        doc.setLineWidth(0.5);
        doc.rect(margin, y, boxWidth, boxHeight);

        const colWidth = boxWidth / 2;
        const leftColX = margin + 5;
        const rightColX = margin + colWidth + 5;
        let detailsY = y + 4;

        doc.setFontSize(fontSizeDetailsLabel);
        doc.setFont(fontBold, 'bold');
        doc.text('Invoice No.:', leftColX, detailsY);
        doc.setFont(fontNormal, 'normal');
        doc.text(`${invoiceData.invoice_number || 'N/A'}`, leftColX + 25, detailsY);
        detailsY += 5;

        detailsY = y + 4;

        doc.setFont(fontBold, 'bold');
        doc.text('Date:', rightColX, detailsY);
        doc.setFont(fontNormal, 'normal');
        doc.text(`${moment(invoiceData.invoice_date).format('DD MMM YYYY')}`, rightColX + 25, detailsY);
        detailsY += 5;

        y += boxHeight + 8;
    }

    function addTableHeaders() {
        doc.setFontSize(fontSizeTableHead);
        doc.setFont(fontBold, 'bold');

        const tableHeaders = [
            'Sr', 'Description of Goods', 'HSN/SAC', 'Qty', 'Rate', 'Per', 'Amount'
        ];
        const headerHeight = 7;

        doc.setFillColor(220, 220, 220);
        doc.rect(margin, y - 5, pageWidth - margin * 2, headerHeight, 'F');

        tableHeaders.forEach((header, index) => {
            const xPos = index === tableHeaders.length - 1
                ? tableXPositions[index + 1] - 2
                : tableXPositions[index] + 2;
            const alignment = index === tableHeaders.length - 1 ? 'right' : 'left';
            doc.text(header, xPos, y, { align: alignment });
        });

        y += headerHeight;
        doc.setDrawColor(0);
        doc.line(margin, y - 5, pageWidth - margin, y - 5);
    }

    function addTableData(items) {
        let srNo = 1;
        let total = 0;

        doc.setFontSize(fontSizeTableBody);
        console.log('Adding table data for items:', items);
        items.forEach(item => {
            const startY = y;
            doc.setFont(fontNormal, 'normal');
            doc.text(srNo.toString(), tableXPositions[0] + 2, y);

            let description = `${item.plateSize} - ${item.colours} ${item.colours === 1 ? 'colour' : 'colours'}`;

            if (item.hasBaking || item.rateType === 'baking_rate' ||
                (item.remarks && item.remarks.toLowerCase().includes('baking'))) {
                description += ' + Baking';
            }

            doc.setFont(fontBold, 'bold');
            doc.text(description, tableXPositions[1] + 2, y);
            y += 4;

            doc.setFont(fontNormal, 'normal');
            // Replace job IDs with challan numbers
            
            const challansList = [...new Set(item.jobs.map(job => job.challan_no))].join(', ');
            console.log('Challans List:', challansList);
            const maxWidth = tableXPositions[2] - tableXPositions[1] - 4;
            const challanLines = doc.splitTextToSize(`${challansList}`, maxWidth);

            challanLines.forEach(line => {
                doc.text(line, tableXPositions[1] + 2, y);
                y += 3.5;
            });

            doc.text('8442', (tableXPositions[2] + tableXPositions[3]) / 2, startY, { align: 'center' });
            doc.text(item.quantity.toString(), (tableXPositions[3] + tableXPositions[4]) / 2, startY, { align: 'center' });

            let rate = 0;
            if (item.plateSizeId && ratesData) {
                if (typeof item.rate === 'number' && !isNaN(item.rate)) {
                    const rateEntry = ratesData.find(r =>
                        r.plate_size_id === item.plateSizeId
                    );

                    if (rateEntry) {
                        const baseRate = parseFloat(rateEntry.plate_rate || 0);
                        const bakingAddition = item.rateType === 'baking_rate' ?
                            parseFloat(rateEntry.baking_rate || 0) : 0;
                        rate = baseRate + bakingAddition;
                        
                        if (item.colours > 1) {
                            rate = rate * (typeof item.colours === 'number' ? item.colours : 1);
                        }
                    } else {
                        rate = parseFloat(item.rate || 0);
                    }                   
                } else {
                    const rateEntry = ratesData.find(r =>
                        r.plate_size_id === item.plateSizeId
                    );

                    if (rateEntry) {
                        const baseRate = parseFloat(rateEntry.plate_rate || 0);
                        const bakingAddition = item.rateType === 'baking_rate' ?
                            parseFloat(rateEntry.baking_rate || 0) : 0;
                        rate = baseRate + bakingAddition;
                        
                        if (item.colours > 1) {
                            rate = rate * (typeof item.colours === 'number' ? item.colours : 1);
                        }
                    } else {
                        rate = parseFloat(item.rate || 0);
                    }
                }
            } else {
                rate = parseFloat(item.rate || 0);
            }

            if (isNaN(rate)) {
                console.warn(`Invalid rate for item: ${JSON.stringify(item)}`);
                rate = 0;
            }

            const rateFormatted = rate.toFixed(1);
            doc.text(`${rateFormatted}`, (tableXPositions[4] + tableXPositions[5]) / 2, startY, { align: 'center' });
            doc.text(`/ Unit`, (tableXPositions[5] + tableXPositions[6]) / 2, startY, { align: 'center' });

            const amount = (item.quantity * rate).toFixed(1);
            total += parseFloat(amount);
            doc.text(`${amount}`, tableXPositions[7] - 2, startY, { align: 'right' });

            doc.setDrawColor(0);
            doc.setLineWidth(0.1);
            tableXPositions.forEach((xPos, index) => {
                doc.line(xPos, startY - 5, xPos, y - 1);
                if (index === tableXPositions.length - 1) {
                    doc.line(pageWidth - margin, startY - 5, pageWidth - margin, y - 1);
                }
            });

            doc.setDrawColor(200, 200, 200);
            doc.setLineWidth(0.1);
            doc.line(margin, y - 1, pageWidth - margin, y - 1);
            y += 4;

            if (y + 15 > pageHeight - margin) {
                doc.addPage();
                y = margin + 10;
                addTableHeaders();
            }

            srNo++;
        });

        return total;
    }

    function addTotalsAndFooter(total) {
        const totalQuantity = itemsData.reduce((sum, item) => sum + item.quantity, 0);
        const cgst = (total * 0.09).toFixed(2);
        const sgst = (total * 0.09).toFixed(2);
        const totalWithTax = (parseFloat(total) + parseFloat(cgst) + parseFloat(sgst)).toFixed(2);
        const exactTotalWithTax = parseFloat(total) + parseFloat(cgst) + parseFloat(sgst);
        const roundedTotal = Math.round(exactTotalWithTax);
        const roundingAdjustment = (roundedTotal - exactTotalWithTax).toFixed(2);

        doc.setDrawColor(0);
        doc.setLineWidth(0.5);
        doc.line(margin, y - 5, pageWidth - margin, y - 5);
        y += 3;

        doc.setFontSize(fontSizeDetailsValue);
        doc.setFont(fontBold, 'bold');
        doc.text('Total Quantity:', margin, y);
        doc.text(`${totalQuantity} Units`, tableXPositions[2] - 10, y, { align: 'right' });
        y += 5;

        doc.setFontSize(fontSizeDetailsValue);
        doc.text('Amount in words:', margin, y);
        y += 5;
        doc.setFont(fontNormal, 'italic');
        const amountInWords = `Rupees ${numberToWords(roundedTotal)} Only`;
        const maxAmountWidth = tableXPositions[2] - 20;
        const wrappedAmountInWords = doc.splitTextToSize(amountInWords, maxAmountWidth);
        wrappedAmountInWords.forEach((line, index) => {
            doc.text(line, margin + 5, y + (index * 4));
        });

        y -= 10;
        doc.setFont(fontBold, 'bold');
        doc.text('Sub Total:', tableXPositions[4] - 30, y);
        doc.text(`${total.toFixed(2)}`, tableXPositions[7], y, { align: 'right' });
        y += 5;

        doc.text('CGST @ 9%:', tableXPositions[4] - 30, y);
        doc.text(`${cgst}`, tableXPositions[7], y, { align: 'right' });
        y += 5;

        doc.text('SGST @ 9%:', tableXPositions[4] - 30, y);
        doc.text(`${sgst}`, tableXPositions[7], y, { align: 'right' });

        doc.setDrawColor(0);
        doc.setLineWidth(0.5);
        doc.line(tableXPositions[4] - 30, y + 1, pageWidth - margin, y + 1);
        y += 5;

        doc.text('Rounding:', tableXPositions[4] - 30, y);
        doc.text(`${roundingAdjustment}`, tableXPositions[7], y, { align: 'right' });
        y += 5;

        doc.text('Total Amount:', tableXPositions[4] - 30, y);
        doc.text(`${roundedTotal.toFixed(2)}`, tableXPositions[7], y, { align: 'right' });
        y += 5;

        addTaxSummaryTable(total, cgst, sgst);
        y += 5;

        const declarationY = pageHeight - 50;
        doc.setFontSize(9);
        doc.setFont(fontBold, 'bold');
        doc.text("Company's PAN : AAAFN9711H", margin, declarationY);

        doc.setFontSize(8);
        doc.setFont(fontBold, 'bold');
        doc.text("Declaration", margin, declarationY + 5);

        doc.setFont(fontNormal, 'normal');
        const declarationText = "We hereby certify that our registration certificate under the Goods & Service Tax is in force from 1st July 2017 on the date on which the sale of goods specified in this Tax Invoice is made by us & that the transaction of sale covered by this Tax Invoice has been affected by us and it shall be accounted for in the turnover of sales while filling of return and the due tax if any payable on the sales has been paid or shall be paid";

        const maxWidth = (pageWidth / 2) - margin - 10;
        const declarationLines = doc.splitTextToSize(declarationText, maxWidth);

        declarationLines.forEach((line, index) => {
            doc.text(line, margin, declarationY + 10 + (index * 3.5), { align: 'justify' });
        });

        const bankDetailsX = pageWidth - margin - 65;
        doc.setFontSize(9);
        doc.setFont(fontBold, 'bold');
        doc.text("Company's Bank Details", bankDetailsX, declarationY);

        doc.setFontSize(8);
        doc.setFont(fontNormal, 'normal');
        doc.text("Bank Name : BANK OF BARODA", bankDetailsX, declarationY + 4);
        doc.text("A/c No. : 04510200000579", bankDetailsX, declarationY + 8);
        doc.text("Branch : Shivaji Nagar, IFS Code : BARB0SHIPOO", bankDetailsX, declarationY + 12);

        y = pageHeight - 35;

        const boxWidth = 70;
        const boxHeight = 25;
        const boxX = pageWidth - margin - boxWidth;
        const boxY = y - 2;

        doc.setDrawColor(0);
        doc.setLineWidth(0.2);
        doc.rect(boxX, boxY, boxWidth, boxHeight);

        doc.setFont(fontNormal, 'bold');
        doc.text('for NEW WAY TYPESETTERS & PROCESSORS', pageWidth - margin - 2, y + 2, { align: 'right' });
    }

    function addTaxSummaryTable(taxableAmount, cgst, sgst) {
        const tableWidth = pageWidth - margin * 2;

        const colWidths = [
            tableWidth * 0.15,
            tableWidth * 0.20,
            tableWidth * 0.10,
            tableWidth * 0.15,
            tableWidth * 0.10,
            tableWidth * 0.15,
            tableWidth * 0.15
        ];

        const colPositions = [margin];
        for (let i = 0; i < colWidths.length; i++) {
            colPositions.push(colPositions[i] + colWidths[i]);
        }

        doc.setFontSize(fontSizeDetailsValue);
        doc.setFont(fontBold, 'bold');
        doc.text('Tax Summary', margin, y);
        y += 6;

        const firstRowHeight = 5;
        doc.setFillColor(220, 220, 220);
        doc.rect(margin, y - 4, tableWidth, firstRowHeight, 'F');

        doc.setFontSize(8);
        doc.setFont(fontBold, 'bold');
        doc.text('HSN/SAC', colPositions[0] + (colWidths[0] / 2), y, { align: 'center' });
        doc.text('Taxable Value', colPositions[1] + (colWidths[1] / 2), y, { align: 'center' });

        const cgstCenter = colPositions[2] + (colWidths[2] + colWidths[3]) / 2;
        doc.text('CGST', cgstCenter, y, { align: 'center' });

        const sgstCenter = colPositions[4] + (colWidths[4] + colWidths[5]) / 2;
        doc.text('SGST', sgstCenter, y, { align: 'center' });

        doc.text('Total Tax Amount', colPositions[6] + (colWidths[6] / 2), y, { align: 'center' });

        y += firstRowHeight;

        const secondRowHeight = 5;
        doc.setFillColor(240, 240, 240);
        doc.rect(margin, y - 4, tableWidth, secondRowHeight, 'F');

        doc.text('Rate %', colPositions[2] + (colWidths[2] / 2), y, { align: 'center' });
        doc.text('Amount', colPositions[3] + (colWidths[3] / 2), y, { align: 'center' });
        doc.text('Rate %', colPositions[4] + (colWidths[4] / 2), y, { align: 'center' });
        doc.text('Amount', colPositions[5] + (colWidths[5] / 2), y, { align: 'center' });

        y += secondRowHeight;

        doc.setDrawColor(0);
        doc.setLineWidth(0.1);

        doc.line(margin, y - secondRowHeight - firstRowHeight - 4, margin + tableWidth, y - secondRowHeight - firstRowHeight - 4);
        doc.line(colPositions[2], y - secondRowHeight - 4, colPositions[6], y - secondRowHeight - 4);
        doc.line(margin, y - 4, margin + tableWidth, y - 4);

        doc.line(margin, y - secondRowHeight - firstRowHeight - 4, margin, y - 4);
        doc.line(colPositions[1], y - secondRowHeight - firstRowHeight - 4, colPositions[1], y - 4);
        doc.line(colPositions[2], y - secondRowHeight - firstRowHeight - 4, colPositions[2], y - 4);
        doc.line(colPositions[3], y - secondRowHeight - 4, colPositions[3], y - 4);
        doc.line(colPositions[4], y - secondRowHeight - firstRowHeight - 4, colPositions[4], y - 4);
        doc.line(colPositions[5], y - secondRowHeight - 4, colPositions[5], y - 4);
        doc.line(colPositions[6], y - secondRowHeight - firstRowHeight - 4, colPositions[6], y - 4);
        doc.line(margin + tableWidth, y - secondRowHeight - firstRowHeight - 4, margin + tableWidth, y - 4);

        const dataRowHeight = 6;
        doc.setFont(fontNormal, 'normal');
        const totalTaxAmount = parseFloat(cgst) + parseFloat(sgst);

        doc.text('8442', colPositions[0] + (colWidths[0] / 2), y, { align: 'center' });
        doc.text(`${taxableAmount.toFixed(2)}`, colPositions[1] + (colWidths[1] / 2), y, { align: 'center' });
        doc.text('9%', colPositions[2] + (colWidths[2] / 2), y, { align: 'center' });
        doc.text(`${cgst}`, colPositions[3] + (colWidths[3] / 2), y, { align: 'center' });
        doc.text('9%', colPositions[4] + (colWidths[4] / 2), y, { align: 'center' });
        doc.text(`${sgst}`, colPositions[5] + (colWidths[5] / 2), y, { align: 'center' });
        doc.text(`${totalTaxAmount.toFixed(2)}`, colPositions[6] + (colWidths[6] / 2), y, { align: 'center' });

        doc.line(margin, y + dataRowHeight - 4, margin + tableWidth, y + dataRowHeight - 4);

        colPositions.forEach(xPos => {
            doc.line(xPos, y - 4, xPos, y + dataRowHeight - 4);
        });

        const taxAmountInWords = `Rupees ${numberToWords(totalTaxAmount)} Only`;

        y += dataRowHeight;
        doc.setFont(fontBold, 'bold');
        doc.text('Tax Amount in Words:', margin, y);
        doc.setFont(fontNormal, 'italic');
        doc.text(taxAmountInWords, margin + 35, y);

        y += 10;
    }

    function numberToWords(num) {
        if (num === 0) return 'Zero';

        const units = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'];
        const teens = ['Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
        const tens = ['', 'Ten', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

        function convertToWords(number) {
            if (number === 0) return '';
            if (number <= 10) return units[number];
            if (number < 20) return teens[number - 11];
            if (number < 100) {
                return tens[Math.floor(number / 10)] + (number % 10 ? ' ' + units[number % 10] : '');
            }
            if (number < 1000) {
                return units[Math.floor(number / 100)] + ' Hundred' + (number % 100 ? ' and ' + convertToWords(number % 100) : '');
            }
            if (number < 100000) {
                return convertToWords(Math.floor(number / 1000)) + ' Thousand' + (number % 1000 ? ' ' + convertToWords(number % 1000) : '');
            }
            if (number < 10000000) {
                return convertToWords(Math.floor(number / 100000)) + ' Lakh' + (number % 100000 ? ' ' + convertToWords(number % 100000) : '');
            }
            if (number < 1000000000) {
                return convertToWords(Math.floor(number / 10000000)) + ' Crore' + (number % 10000000 ? ' ' + convertToWords(number % 10000000) : '');
            }
            return 'Very Large Number';
        }

        const wholePart = Math.floor(num);
        const decimalPart = Math.round((num - wholePart) * 100);

        let result = convertToWords(wholePart);
        if (decimalPart) {
            result += ' and ' + convertToWords(decimalPart) + ' Paise';
        }

        return result;
    }

    function addWatermark() {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = function() {
                const centerX = pageWidth / 2;
                const centerY = pageHeight / 2;
                const maxDimension = Math.min(pageWidth, pageHeight) * 0.5;
                const aspectRatio = img.width / img.height;

                let watermarkWidth, watermarkHeight;
                if (aspectRatio > 1) {
                    watermarkWidth = maxDimension;
                    watermarkHeight = maxDimension / aspectRatio;
                } else {
                    watermarkHeight = maxDimension;
                    watermarkWidth = maxDimension * aspectRatio;
                }

                doc.saveGraphicsState();
                doc.setGState(new doc.GState({ opacity: 0.05 }));
                doc.addImage(
                    img,
                    'PNG',
                    centerX - (watermarkWidth / 2),
                    centerY - (watermarkHeight / 2),
                    watermarkWidth,
                    watermarkHeight
                );
                doc.restoreGraphicsState();
                resolve();
            };

            img.onerror = function() {
                console.error('Failed to load watermark logo');
                resolve();
            };

            const publicPath = '/images/NewWayLogo.png';
            try {
                if (newWayLogo) {
                    img.src = newWayLogo;
                } else {
                    img.src = publicPath;
                }
            } catch (error) {
                console.error('Error loading watermark:', error);
                img.src = publicPath;
            }
        });
    }

    function generateFinalPDF() {
        const y = pageHeight - 35;
        const boxWidth = 90;
        const boxHeight = 25;
        const boxX = pageWidth - margin - boxWidth;
        const boxY = y - 2;

        return new Promise((resolve) => {
            addWatermark().then(() => {
                const signatureImageUrl = '/images/InvoiceSignature2.png';
                // console.log('Using signature path:', signatureImageUrl);

                const img = new Image();
                img.crossOrigin = 'Anonymous';

                img.onload = function() {
                    // console.log('Signature loaded successfully', img.width, 'x', img.height);

                    addTotalsAndFooter(totalAmount);

                    try {
                        const originalAspectRatio = img.width / img.height;
                        const maxHeight = 20;
                        const calculatedWidth = maxHeight * originalAspectRatio;
                        const signatureTextPosition = pageWidth - margin - 2;
                        const signatureTextWidth = 40;
                        const xOffset = signatureTextPosition - signatureTextWidth - calculatedWidth + 10;

                        doc.addImage(img, 'PNG', xOffset, y + 2, calculatedWidth, maxHeight);
                        doc.text('Authorized Signatory', pageWidth - margin - 2, y + 20, { align: 'right' });
                    } catch (err) {
                        console.error('Failed to add signature:', err);
                        doc.text('Authorized Signatory', pageWidth - margin - 2, y + 20, { align: 'right' });
                    }

                    if (shouldPrint) {
                        doc.autoPrint();
                    }
                    window.open(doc.output('bloburl'), '_blank');
                    resolve(doc.output('blob'));
                };

                img.onerror = function() {
                    console.error('Failed to load signature image');
                    addTotalsAndFooter(totalAmount);
                    if (shouldPrint) {
                        doc.autoPrint();
                    }
                    window.open(doc.output('bloburl'), '_blank');
                    resolve(doc.output('blob'));
                };

                img.src = signatureImageUrl;
            });
        });
    }

    addHeader();
    addInvoiceDetails();
    addTableHeaders();
    const totalAmount = addTableData(itemsData);

    return generateFinalPDF();
}
