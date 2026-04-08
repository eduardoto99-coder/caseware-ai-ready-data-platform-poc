db = db.getSiblingDB("caseware_documents");

db.audit_documents.insertMany([
  {
    _id: "doc_alpha_policy_revrec",
    tenant_id: "tenant_alpha",
    document_id: "doc_alpha_policy_revrec",
    title: "Revenue Recognition Policy",
    doc_type: "policy",
    classification: "confidential",
    retention_state: "active",
    updated_at: new Date(),
    source_uri: "s3://tenant-alpha/policies/revenue-recognition-policy-v3.pdf",
    text: "Deferred revenue is recognized when contractual performance obligations are satisfied."
  },
  {
    _id: "doc_alpha_workpaper_ocr",
    tenant_id: "tenant_alpha",
    document_id: "doc_alpha_workpaper_ocr",
    title: "Revenue Workpaper OCR Export",
    doc_type: "workpaper",
    classification: "confidential",
    retention_state: "active",
    updated_at: new Date(),
    source_uri: "s3://tenant-alpha/workpapers/revenue/workpaper-ocr-export.txt",
    text: "Observed table. Onboarding services. Recognize over service period. Numeric values are not authoritative."
  },
  {
    _id: "doc_beta_policy_defrev",
    tenant_id: "tenant_beta",
    document_id: "doc_beta_policy_defrev",
    title: "Deferred Revenue Accounting Policy",
    doc_type: "policy",
    classification: "confidential",
    retention_state: "active",
    updated_at: new Date(),
    source_uri: "s3://tenant-beta/policies/deferred-revenue-accounting.md",
    text: "Implementation fees are not recognized upfront when they are not distinct from the recurring monitoring service."
  }
]);

