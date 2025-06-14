import jsPDF from 'jspdf';
import { printTaxInvoice } from './printTaxInvoice';

export async function generatePDF(invoiceData, customerData, itemsData, ratesData) {
  return new Promise(async (resolve, reject) => {
    try {
      // Create a silent version of window.open to prevent pdf from opening in browser
      const originalWindowOpen = window.open;
      window.open = function(url, target) {
        if (url && url.startsWith('blob:') && target === '_blank') {
          // Silently capture the call but don't open the window
          return null;
        }
        // Pass through any other window.open calls
        return originalWindowOpen.apply(window, arguments);
      };

      try {
        // Generate the PDF blob without opening it
        const pdfBlob = await printTaxInvoice(invoiceData, customerData, itemsData, ratesData, false);
        
        // Convert blob to base64
        const reader = new FileReader();
        reader.onload = () => {
          const base64data = reader.result;
          const base64Content = base64data.split(',')[1]; // Remove the data URL prefix
          resolve(base64Content);
        };
        reader.onerror = () => reject(new Error('Failed to convert PDF to base64'));
        reader.readAsDataURL(pdfBlob);
      } finally {
        // Restore original window.open function
        window.open = originalWindowOpen;
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      reject(error);
    }
  });
}