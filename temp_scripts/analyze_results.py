import csv

# Open your CSV file
with open('verified_outputs/hurricane_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    dino_correct = 0
    vqa_correct = 0
    agreement = 0
    total = 0
    
    for row in reader:
        # Extract the columns (handling uppercase/lowercase safely)
        gt = row.get('ground_truth', '').lower().strip()
        dino = row.get('predicted_class', '').lower().strip()
        vqa_raw = row.get('structural_assessment', '').lower().strip()
        
        # Phi-3-Vision sometimes adds extra punctuation or text, so we clean it
        vqa = 'unknown'
        if 'damaged' in vqa_raw and 'intact' not in vqa_raw:
            vqa = 'damaged'
        elif 'intact' in vqa_raw and 'damaged' not in vqa_raw:
            vqa = 'intact'
        elif vqa_raw in ['damaged', 'intact']:
            vqa = vqa_raw

        if vqa == 'damaged' : vqa = 'damage'
        if vqa == 'intact' : vqa = 'no_damage'
            
        # Calculate the metrics!
        if dino == gt:
            dino_correct += 1
        if vqa == gt:
            vqa_correct += 1
        if dino == vqa:
            agreement += 1
            
        total += 1

print(f"Total rows analyzed: {total}")
print(f"DINO Accuracy (Classification): {dino_correct/total*100:.2f}%")
print(f"VQA Accuracy (Phi-3-Vision): {vqa_correct/total*100:.2f}%")
print(f"DINO and VQA Agreement: {agreement/total*100:.2f}%")
