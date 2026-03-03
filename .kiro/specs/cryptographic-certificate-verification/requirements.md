# Requirements Document

## Introduction

The EduCerts system currently has a critical security vulnerability: when a user downloads a signed certificate PDF, modifies its content (e.g., changing the student name, grade, or course), and re-uploads it for verification, the system incorrectly reports it as "verified." This occurs because verification only checks if the certificate ID exists in the database, without validating that the PDF content matches what was originally issued.

This feature will implement cryptographic verification that detects any tampering with certificate PDFs by embedding a cryptographic hash of the PDF content and validating it during verification.

## Glossary

- **Certificate System**: The EduCerts backend application that issues and verifies educational certificates
- **PDF Document**: A Portable Document Format file containing certificate information
- **Cryptographic Hash**: A one-way mathematical function that produces a unique fixed-size string from input data
- **Digital Signature**: A cryptographic value calculated from the PDF content and signed with a private key
- **Tamper Detection**: The process of identifying unauthorized modifications to a document
- **Content Hash**: A SHA-256 hash computed from the visual and textual content of a PDF
- **Verification Endpoint**: The API endpoint `/api/verify/pdf` that validates uploaded certificates
- **Document Registry**: The database table storing merkle roots and certificate batch information

## Requirements

### Requirement 1

**User Story:** As a certificate verifier, I want the system to detect any modifications to certificate PDFs, so that I can trust that tampered documents will be rejected.

#### Acceptance Criteria

1. WHEN a certificate PDF is generated THEN the Certificate System SHALL compute a cryptographic hash of the PDF content and store it in the database
2. WHEN a user uploads a PDF for verification THEN the Certificate System SHALL compute the hash of the uploaded PDF and compare it to the stored hash
3. WHEN the computed hash does not match the stored hash THEN the Certificate System SHALL return a verification failure with status "INVALID" for document integrity
4. WHEN the computed hash matches the stored hash THEN the Certificate System SHALL proceed with other verification checks
5. WHEN a user modifies any text content in a certificate PDF THEN the content hash SHALL change and verification SHALL fail

### Requirement 2

**User Story:** As a system administrator, I want certificate PDFs to include embedded cryptographic signatures, so that tampering can be detected even if the database is unavailable.

#### Acceptance Criteria

1. WHEN a certificate PDF is generated THEN the Certificate System SHALL embed a cryptographic signature in the PDF metadata
2. WHEN a certificate PDF is generated THEN the Certificate System SHALL include the certificate ID in the PDF metadata subject field
3. WHEN verifying a PDF THEN the Certificate System SHALL extract the embedded signature from PDF metadata
4. WHEN the embedded signature is missing or invalid THEN the Certificate System SHALL return a verification failure
5. WHEN the PDF metadata has been modified THEN the Certificate System SHALL detect the tampering through signature validation

### Requirement 3

**User Story:** As a developer, I want the hash computation to be deterministic and content-based, so that identical visual certificates produce identical hashes.

#### Acceptance Criteria

1. WHEN computing a PDF hash THEN the Certificate System SHALL extract text content from all pages
2. WHEN computing a PDF hash THEN the Certificate System SHALL normalize whitespace and line endings
3. WHEN computing a PDF hash THEN the Certificate System SHALL use SHA-256 as the hashing algorithm
4. WHEN two PDFs have identical text content THEN the Certificate System SHALL produce identical content hashes
5. WHEN a PDF contains only metadata changes THEN the content hash SHALL remain unchanged

### Requirement 4

**User Story:** As a certificate issuer, I want the system to store content hashes for all issued certificates, so that verification can detect tampering.

#### Acceptance Criteria

1. WHEN a certificate is issued THEN the Certificate System SHALL compute and store the content hash in the certificates table
2. WHEN a certificate PDF is signed THEN the Certificate System SHALL recompute and update the content hash
3. WHEN storing a content hash THEN the Certificate System SHALL use a dedicated database column named content_hash
4. WHEN a certificate is revoked THEN the Certificate System SHALL retain the content hash for audit purposes
5. WHEN querying a certificate THEN the Certificate System SHALL return the stored content hash in the response

### Requirement 5

**User Story:** As a security auditor, I want verification failures to provide detailed information about what failed, so that I can understand the nature of potential tampering.

#### Acceptance Criteria

1. WHEN verification fails due to hash mismatch THEN the Certificate System SHALL return a detailed error message indicating "Content has been modified"
2. WHEN verification fails THEN the Certificate System SHALL include both the expected hash and computed hash in the response
3. WHEN verification succeeds THEN the Certificate System SHALL return all verification checks with their individual statuses
4. WHEN a PDF cannot be parsed THEN the Certificate System SHALL return a clear error message indicating the file is corrupted or invalid
5. WHEN verification is performed THEN the Certificate System SHALL log the verification attempt with timestamp and result

### Requirement 6

**User Story:** As a system integrator, I want the verification API to support both ID-based and PDF upload verification, so that different verification workflows are supported.

#### Acceptance Criteria

1. WHEN verifying by certificate ID THEN the Certificate System SHALL retrieve the stored content hash and compare it to the stored PDF file
2. WHEN verifying by PDF upload THEN the Certificate System SHALL extract the certificate ID from the PDF and retrieve the stored hash
3. WHEN a certificate ID is not found THEN the Certificate System SHALL return a 404 error with message "Certificate not found"
4. WHEN a PDF upload contains no valid certificate ID THEN the Certificate System SHALL return a 400 error with message "Could not find a valid Certificate ID"
5. WHEN both verification methods are used for the same certificate THEN the Certificate System SHALL return consistent results

### Requirement 7

**User Story:** As a developer, I want the hash computation to be efficient and not block the issuance process, so that certificate generation remains fast.

#### Acceptance Criteria

1. WHEN computing a content hash THEN the Certificate System SHALL complete the operation in less than 500 milliseconds for PDFs under 5MB
2. WHEN a PDF is larger than 5MB THEN the Certificate System SHALL still compute the hash without timing out
3. WHEN multiple certificates are issued in batch THEN the Certificate System SHALL compute hashes in parallel where possible
4. WHEN hash computation fails THEN the Certificate System SHALL log the error and continue with certificate issuance
5. WHEN the system is under load THEN hash computation SHALL not cause request timeouts

### Requirement 8

**User Story:** As a certificate recipient, I want to verify my certificate immediately after download, so that I can confirm it has not been corrupted during transfer.

#### Acceptance Criteria

1. WHEN a user downloads a certificate PDF THEN the Certificate System SHALL provide a verification link or QR code
2. WHEN a user uploads the downloaded PDF for verification THEN the Certificate System SHALL confirm it matches the issued version
3. WHEN verification succeeds THEN the Certificate System SHALL display a success message with certificate details
4. WHEN verification fails THEN the Certificate System SHALL display a clear warning that the document may have been tampered with
5. WHEN a certificate is verified multiple times THEN the Certificate System SHALL return consistent results
