# SLR tool for automated and comprehensive reviews

Databases to support:
- Scopus
- IEEE Xplore
- ACM
- etc.

Process:
- Define one search query, databases to look in and Inclusion/Exclusion criteria, e.g data range, keywords, subject areas, minimum citation count, publication type, etc.
- Query all databases, transform query / exclusion criteria if not supported by specific database or mimic using another method
- Use crossref to find important missing metadata (e.g. used for inclusion/exclusion)
- Perform automated forward backward search
- Maybe ask for missing data using popup to create a semi-automated process in case of important missing meta data
- Export results
- Create diagrams visualizing results based on selection criteria using matplotlib or similar
