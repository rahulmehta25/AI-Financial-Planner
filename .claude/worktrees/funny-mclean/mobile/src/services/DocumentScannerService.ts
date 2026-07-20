import DocumentScanner from 'react-native-document-scanner-plugin';
import {Platform, Alert, PermissionsAndroid} from 'react-native';
import RNFS from 'react-native-fs';
import {Document, DocumentType, CameraConfig} from '@types/common';
import {DOCUMENT_SCANNER_CONFIG, CAMERA_CONFIG} from '@constants/config';
import {HapticService} from './HapticService';

export interface ScanResult {
  success: boolean;
  uri?: string;
  error?: string;
  extractedData?: any;
}

export interface ScanOptions {
  quality?: number;
  croppingEnabled?: boolean;
  responseType?: 'imageFilePath' | 'base64';
  overlayColor?: string;
}

class DocumentScannerServiceClass {
  /**
   * Check if document scanner is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      // Check camera permissions
      const hasPermission = await this.checkCameraPermission();
      return hasPermission;
    } catch (error) {
      console.error('Error checking document scanner availability:', error);
      return false;
    }
  }

  /**
   * Request camera permissions
   */
  async requestCameraPermission(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        // iOS permissions are handled in Info.plist
        return true;
      } else {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.CAMERA,
          {
            title: 'Camera Permission',
            message: 'Financial Planner needs access to your camera to scan documents.',
            buttonNeutral: 'Ask Me Later',
            buttonNegative: 'Cancel',
            buttonPositive: 'OK',
          }
        );
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      }
    } catch (error) {
      console.error('Error requesting camera permission:', error);
      return false;
    }
  }

  /**
   * Check camera permissions
   */
  async checkCameraPermission(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        // On iOS, we assume permission is granted if the app is running
        // In a real app, you might want to check more thoroughly
        return true;
      } else {
        const granted = await PermissionsAndroid.check(
          PermissionsAndroid.PERMISSIONS.CAMERA
        );
        return granted;
      }
    } catch (error) {
      console.error('Error checking camera permission:', error);
      return false;
    }
  }

  /**
   * Scan document with camera
   */
  async scanDocument(options?: ScanOptions): Promise<ScanResult> {
    try {
      // Check permissions first
      const hasPermission = await this.checkCameraPermission();
      if (!hasPermission) {
        const granted = await this.requestCameraPermission();
        if (!granted) {
          return {
            success: false,
            error: 'Camera permission not granted',
          };
        }
      }

      // Configure scanner options
      const scannerOptions = {
        ...DOCUMENT_SCANNER_CONFIG,
        ...options,
      };

      // Trigger haptic feedback before scanning
      await HapticService.light();

      // Start document scanning
      const result = await DocumentScanner.scanDocument(scannerOptions);

      if (result.scannedImages && result.scannedImages.length > 0) {
        const scannedImageUri = result.scannedImages[0];
        
        // Trigger success haptic feedback
        await HapticService.success();

        return {
          success: true,
          uri: scannedImageUri,
        };
      } else {
        return {
          success: false,
          error: 'No document scanned',
        };
      }
    } catch (error: any) {
      console.error('Document scanning error:', error);
      
      // Trigger error haptic feedback
      await HapticService.error();

      return {
        success: false,
        error: error.message || 'Document scanning failed',
      };
    }
  }

  /**
   * Scan multiple documents
   */
  async scanMultipleDocuments(count: number = 5, options?: ScanOptions): Promise<ScanResult[]> {
    const results: ScanResult[] = [];

    for (let i = 0; i < count; i++) {
      try {
        const result = await this.scanDocument({
          ...options,
          // Add page indicator in overlay
          overlayColor: 'rgba(255, 255, 255, 0.3)',
        });

        results.push(result);

        // If scanning failed or user cancelled, stop
        if (!result.success) {
          break;
        }

        // Ask user if they want to continue scanning
        if (i < count - 1) {
          const shouldContinue = await this.askToContinueScanning(i + 1, count);
          if (!shouldContinue) {
            break;
          }
        }
      } catch (error) {
        console.error('Error scanning document:', error);
        results.push({
          success: false,
          error: 'Scanning failed',
        });
        break;
      }
    }

    return results;
  }

  /**
   * Process scanned document
   */
  async processScannedDocument(
    uri: string, 
    documentType: DocumentType, 
    metadata?: any
  ): Promise<Document> {
    try {
      // Get file info
      const fileInfo = await RNFS.stat(uri);
      
      // Generate unique filename
      const timestamp = Date.now();
      const extension = uri.split('.').pop() || 'jpg';
      const filename = `${documentType}_${timestamp}.${extension}`;

      // Create document object
      const document: Document = {
        id: `doc_${timestamp}`,
        name: filename,
        type: documentType,
        uri,
        mimeType: this.getMimeType(extension),
        size: fileInfo.size,
        uploadedAt: new Date().toISOString(),
        extractedData: metadata,
      };

      // Perform OCR or data extraction if needed
      if (this.shouldExtractData(documentType)) {
        const extractedData = await this.extractDataFromDocument(uri, documentType);
        document.extractedData = extractedData;
      }

      return document;
    } catch (error) {
      console.error('Error processing scanned document:', error);
      throw error;
    }
  }

  /**
   * Extract data from document using OCR
   */
  private async extractDataFromDocument(uri: string, type: DocumentType): Promise<any> {
    try {
      // In a real app, you would integrate with an OCR service
      // For now, return mock extracted data based on document type
      
      switch (type) {
        case 'bank_statement':
          return {
            accountNumber: '****1234',
            balance: '$1,234.56',
            statementDate: new Date().toISOString().split('T')[0],
            transactions: [],
          };
        
        case 'pay_stub':
          return {
            employerName: 'Sample Company',
            grossPay: '$5,000.00',
            netPay: '$3,800.00',
            payPeriod: new Date().toISOString().split('T')[0],
          };
        
        case 'tax_document':
          return {
            taxYear: new Date().getFullYear() - 1,
            totalIncome: '$60,000.00',
            taxesPaid: '$8,000.00',
          };
        
        case 'investment_statement':
          return {
            accountValue: '$25,000.00',
            gains: '$2,500.00',
            statementDate: new Date().toISOString().split('T')[0],
          };
        
        default:
          return {
            documentType: type,
            scanDate: new Date().toISOString(),
          };
      }
    } catch (error) {
      console.error('Error extracting data from document:', error);
      return null;
    }
  }

  /**
   * Get MIME type for file extension
   */
  private getMimeType(extension: string): string {
    const mimeTypes: Record<string, string> = {
      jpg: 'image/jpeg',
      jpeg: 'image/jpeg',
      png: 'image/png',
      pdf: 'application/pdf',
    };

    return mimeTypes[extension.toLowerCase()] || 'application/octet-stream';
  }

  /**
   * Check if data extraction should be performed
   */
  private shouldExtractData(type: DocumentType): boolean {
    const extractableTypes: DocumentType[] = [
      'bank_statement',
      'pay_stub',
      'tax_document',
      'investment_statement',
    ];

    return extractableTypes.includes(type);
  }

  /**
   * Ask user if they want to continue scanning
   */
  private async askToContinueScanning(current: number, total: number): Promise<boolean> {
    return new Promise((resolve) => {
      Alert.alert(
        'Continue Scanning?',
        `You've scanned ${current} of ${total} documents. Would you like to scan another?`,
        [
          {
            text: 'Stop',
            style: 'cancel',
            onPress: () => resolve(false),
          },
          {
            text: 'Continue',
            onPress: () => resolve(true),
          },
        ]
      );
    });
  }

  /**
   * Validate scanned document
   */
  validateDocument(uri: string): Promise<{valid: boolean; issues: string[]}> {
    return new Promise(async (resolve) => {
      const issues: string[] = [];

      try {
        // Check if file exists
        const exists = await RNFS.exists(uri);
        if (!exists) {
          issues.push('File does not exist');
        }

        // Check file size
        const fileInfo = await RNFS.stat(uri);
        if (fileInfo.size > CAMERA_CONFIG.MAX_FILE_SIZE) {
          issues.push('File size too large');
        }

        if (fileInfo.size < 1024) {
          issues.push('File size too small');
        }

        // Check file type
        const extension = uri.split('.').pop()?.toLowerCase();
        if (!extension || !CAMERA_CONFIG.ALLOWED_TYPES.includes(extension)) {
          issues.push('Invalid file type');
        }

        resolve({
          valid: issues.length === 0,
          issues,
        });
      } catch (error) {
        console.error('Error validating document:', error);
        resolve({
          valid: false,
          issues: ['Validation failed'],
        });
      }
    });
  }

  /**
   * Compress scanned image
   */
  async compressImage(uri: string, quality: number = 0.8): Promise<string> {
    try {
      // In a real app, you would use an image compression library
      // For now, return the original URI
      console.log('Compressing image:', uri, 'quality:', quality);
      return uri;
    } catch (error) {
      console.error('Error compressing image:', error);
      return uri;
    }
  }

  /**
   * Get supported document types
   */
  getSupportedDocumentTypes(): DocumentType[] {
    return [
      'bank_statement',
      'pay_stub',
      'tax_document',
      'investment_statement',
      'insurance_policy',
      'receipt',
      'other',
    ];
  }

  /**
   * Get document type display name
   */
  getDocumentTypeDisplayName(type: DocumentType): string {
    const displayNames: Record<DocumentType, string> = {
      bank_statement: 'Bank Statement',
      pay_stub: 'Pay Stub',
      tax_document: 'Tax Document',
      investment_statement: 'Investment Statement',
      insurance_policy: 'Insurance Policy',
      receipt: 'Receipt',
      other: 'Other Document',
    };

    return displayNames[type] || 'Unknown Document';
  }
}

export const DocumentScannerService = new DocumentScannerServiceClass();