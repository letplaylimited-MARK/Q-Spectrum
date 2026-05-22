DROP VIEW IF EXISTS v_document_inventory;
CREATE VIEW v_document_inventory AS
SELECT
    document_type,
    COUNT(*) AS document_count
FROM documents
GROUP BY document_type
ORDER BY document_type;
