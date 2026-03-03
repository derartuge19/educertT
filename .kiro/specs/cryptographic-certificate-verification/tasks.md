# Implementation Plan

- [ ] 1. Database schema migration
  - [x] 1.1 Create migration script to add content_hash column


    - Add VARCHAR(64) column to certificates table
    - Create index on content_hash for performance
    - Make column nullable to support legacy certificates
    - _Requirements: 4.3_
  

  - [ ] 1.2 Create rollback script for migration
    - Drop index if exists
    - Drop content_hash column
    - _Requirements: 4.3_


  
  - [ ] 1.3 Run migration on development database
    - Execute upgrade script
    - Verify schema changes
    - Test rollback script


    - _Requirements: 4.3_

- [ ] 2. Implement PDF hash utility module
  - [ ] 2.1 Create pdf_hash_utils.py module
    - Implement compute_pdf_content_hash function
    - Implement normalize_pdf_text function
    - Use PyMuPDF for text extraction
    - Use hashlib.sha256 for hashing
    - _Requirements: 1.1, 3.1, 3.2, 3.3_
  
  - [ ] 2.2 Write property test for hash computation
    - **Property 1: Hash computation and storage during issuance**
    - **Validates: Requirements 1.1, 4.1**
  
  - [ ] 2.3 Write property test for whitespace normalization
    - **Property 9: Whitespace normalization consistency**
    - **Validates: Requirements 3.2, 3.4**

  
  - [ ] 2.4 Write property test for multi-page extraction
    - **Property 8: Multi-page content extraction**
    - **Validates: Requirements 3.1**
  
  - [ ] 2.5 Implement embed_hash_in_pdf_metadata function
    - Use PyMuPDF to set PDF metadata
    - Embed content_hash in custom metadata field
    - Embed cert_id in subject field

    - _Requirements: 2.1, 2.2_
  
  - [ ] 2.6 Write property test for metadata embedding
    - **Property 5: Metadata embedding completeness**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ] 2.7 Implement extract_hash_from_pdf_metadata function
    - Extract content_hash from metadata
    - Extract cert_id from subject field
    - Return dict with both values
    - Handle missing metadata gracefully
    - _Requirements: 2.3_
  
  - [ ] 2.8 Write property test for metadata extraction
    - **Property 6: Metadata extraction during verification**
    - **Validates: Requirements 2.3**
  


  - [ ] 2.9 Write unit tests for error handling
    - Test corrupted PDF handling
    - Test empty PDF handling
    - Test missing metadata handling
    - _Requirements: 5.4_


- [ ] 3. Update certificate issuance endpoint
  - [ ] 3.1 Modify /api/issue endpoint to compute hash
    - Import pdf_hash_utils module
    - Compute hash after PDF generation
    - Store hash in db_cert.content_hash
    - Handle hash computation errors gracefully
    - _Requirements: 1.1, 4.1, 7.4_
  
  - [ ] 3.2 Add hash embedding to PDF during issuance
    - Call embed_hash_in_pdf_metadata after PDF generation
    - Pass content_hash and cert_id
    - Log any embedding errors
    - _Requirements: 2.1, 2.2_
  
  - [ ] 3.3 Write property test for issuance with hash
    - **Property 1: Hash computation and storage during issuance**
    - **Validates: Requirements 1.1, 4.1**
  
  - [ ] 3.4 Write property test for graceful failure
    - **Property 17: Graceful hash computation failure**
    - **Validates: Requirements 7.4**

- [ ] 4. Update certificate signing endpoint
  - [ ] 4.1 Modify signature application to recompute hash
    - Recompute hash after applying signatures
    - Update cert.content_hash in database
    - Update PDF metadata with new hash
    - _Requirements: 4.2_
  
  - [ ] 4.2 Write property test for hash update after signing
    - **Property 11: Hash update after signing**


    - **Validates: Requirements 4.2**
  
  - [ ] 4.3 Write property test for metadata-only changes
    - **Property 10: Metadata-only changes preserve content hash**
    - **Validates: Requirements 3.5**

- [x] 5. Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement enhanced verification endpoint
  - [ ] 6.1 Update /api/verify/pdf to validate content hash
    - Save uploaded file to temporary location
    - Extract cert_id from PDF
    - Compute hash of uploaded PDF
    - Retrieve certificate from database
    - Compare uploaded_hash with cert.content_hash
    - Clean up temporary file
    - _Requirements: 1.2, 1.3, 6.2_
  
  - [ ] 6.2 Add content integrity check to verification response
    - Add CONTENT_INTEGRITY check to response data
    - Include expected and computed hashes
    - Set status to VALID or INVALID based on match
    - Update summary.contentIntegrity field
    - _Requirements: 5.2, 5.3_

  
  - [ ] 6.3 Write property test for tamper detection
    - **Property 2: Tamper detection through hash mismatch**
    - **Validates: Requirements 1.3, 1.5**
  
  - [ ] 6.4 Write property test for unmodified certificates
    - **Property 4: Unmodified certificates pass verification**
    - **Validates: Requirements 1.4**
  
  - [ ] 6.5 Write property test for hash comparison
    - **Property 3: Hash comparison during verification**
    - **Validates: Requirements 1.2, 6.2**
  
  - [ ] 6.6 Handle legacy certificates without hashes
    - Check if cert.content_hash is None
    - Skip content integrity check if null
    - Log warning for legacy certificate
    - Continue with other verification checks
    - _Requirements: 1.4_
  
  - [ ] 6.7 Write unit tests for error cases
    - Test certificate not found (404)
    - Test invalid PDF (400)
    - Test missing cert ID (400)
    - _Requirements: 6.3, 6.4_



- [ ] 7. Add verification logging
  - [x] 7.1 Implement verification logging

    - Log timestamp, cert_id, operation, result
    - Log hash values (first 8 chars)
    - Log error details on failure
    - Use Python logging module
    - _Requirements: 5.5_
  
  - [ ] 7.2 Write property test for logging
    - **Property 15: Verification logging**

    - **Validates: Requirements 5.5**

- [ ] 8. Update certificate query endpoints
  - [ ] 8.1 Add content_hash to certificate response schema
    - Update schemas.Certificate model
    - Include content_hash in serialization
    - _Requirements: 4.5_
  
  - [x] 8.2 Verify hash is returned in /api/certificates endpoint

    - Test that content_hash appears in response
    - _Requirements: 4.5_
  
  - [ ] 8.3 Write property test for hash inclusion
    - **Property 13: Hash inclusion in query responses**
    - **Validates: Requirements 4.5**

- [ ] 9. Implement certificate revocation with hash persistence
  - [ ] 9.1 Verify revocation doesn't delete hash
    - Review /api/revoke/{cert_id} endpoint
    - Ensure content_hash is not modified
    - _Requirements: 4.4_
  
  - [ ] 9.2 Write property test for hash persistence
    - **Property 12: Hash persistence after revocation**
    - **Validates: Requirements 4.4**

- [ ] 10. Add QR code verification link
  - [ ] 10.1 Ensure QR codes are generated with verification links
    - Review existing QR code generation
    - Verify link format includes cert_id
    - _Requirements: 8.1_
  
  - [ ] 10.2 Write property test for QR code presence
    - **Property 18: QR code presence in issued certificates**
    - **Validates: Requirements 8.1**

- [ ] 11. Implement verification consistency tests
  - [x] 11.1 Write property test for verification method consistency



    - **Property 16: Verification method consistency**
    - **Validates: Requirements 6.5**
  
  - [ ] 11.2 Write property test for verification idempotence
    - **Property 19: Verification idempotence**
    - **Validates: Requirements 8.2, 8.5**
  
  - [ ] 11.3 Write property test for metadata tampering detection
    - **Property 7: Metadata tampering detection**
    - **Validates: Requirements 2.5**
  
  - [ ] 11.4 Write property test for verification response completeness
    - **Property 14: Verification response completeness**
    - **Validates: Requirements 5.2, 5.3**

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Create backfill script for legacy certificates
  - [ ] 13.1 Implement backfill_content_hashes.py script
    - Query certificates with null content_hash
    - Compute hash for existing PDFs
    - Update database records
    - Log progress and errors
    - _Requirements: 4.1_
  
  - [ ] 13.2 Write unit tests for backfill script
    - Test with sample legacy certificates
    - Test error handling for missing files
    - _Requirements: 4.1_

- [ ] 14. Update API documentation
  - [ ] 14.1 Document new verification response fields
    - Document CONTENT_INTEGRITY check
    - Document expected/computed hash fields
    - Update API examples
    - _Requirements: 5.2, 5.3_
  
  - [ ] 14.2 Document content_hash field in certificate schema
    - Add field description
    - Note nullable for legacy certificates
    - _Requirements: 4.3, 4.5_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
