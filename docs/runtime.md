# **Time Complexity Analysis of the S3 File Moving Script**

## **1. Listing Objects in S3**
- AWS S3 `list_objects_v2` retrieves all objects with a given prefix.
- This operation runs in **O(N)** time, where **N** is the number of objects.

## **2. Filtering Matching Files**
- The script filters objects using a regex pattern.
- Since each file is checked once, this runs in **O(N)** time.

## **3. Moving Files (Copy + Delete)**
- Each matching file undergoes:
  - **Copying**: **O(1)** (AWS S3 handles the copy internally).
  - **Deleting**: **O(1)**.
- If there are **M** matching files, the overall complexity for moving is **O(M)**.

## **4. Folder Creation**
- Each unique docket ID results in ~15 folder creation operations.
- If there are **D** unique dockets, folder creation takes **O(D)** time.

## **Overall Time Complexity**
\[
O(N + M + D)
\]
- Since **M ≤ N** and **D ≤ N**, we simplify to:
\[
O(N)
\]
where **N** is the total number of files in the source folder.
