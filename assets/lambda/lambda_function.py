import json
import boto3
import uuid
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

# Configuration
S3_BUCKET = "student-participation-records-po2"
TABLE_NAME = "participationRecordsEmail-po2"
table = dynamodb.Table(TABLE_NAME)

REFERENCE_FACE_IMAGE = "faces1_Feb17.jpg"
REFERENCE_NAMES_IMAGE = "names1_Feb17.jpg"

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        action = body.get('action')

        if action == 'generate_presigned_url':
            return generate_presigned_url(body)

        elif action == 'process_participation':
            return process_participation(body)

        else:
            return {"statusCode": 400, "body": json.dumps("Invalid action")}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(str(e))}


def generate_presigned_url(body):
    """ Generate a pre-signed URL for S3 upload """
    file_name = f"{uuid.uuid4()}-{body.get('image_name')}"  # Unique file name
    content_type = body.get('content_type')

    url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': S3_BUCKET, 'Key': file_name, 'ContentType': content_type},
        ExpiresIn=300  # 5 minutes
    )

    return {"statusCode": 200, "body": json.dumps({"url": url, "key": file_name})}


def process_participation(body):
    """ Process image for participation record """
    image_key = body.get('image_key')
    student_name = body.get('name')
    student_email = body.get('email')
    meeting_date = body.get('meeting_date')
    image_type = body.get('image_type')

    if not all([image_key, student_name, student_email, meeting_date, image_type]):
        return {"statusCode": 400, "body": json.dumps("Missing parameters")}

    match_found = False
    if image_type == "face":
        match_found = compare_faces(S3_BUCKET, image_key, S3_BUCKET, REFERENCE_FACE_IMAGE)
    elif image_type == "name":
        match_found = check_name_in_text(S3_BUCKET, image_key, student_name)

    if match_found:
        record_participation(student_name, student_email, meeting_date)
        return {"statusCode": 200, "body": json.dumps("Participation recorded")}

    else:
        return {"statusCode": 404, "body": json.dumps("No match found")}


def compare_faces(source_bucket, source_key, target_bucket, target_key):
    """ Compares the uploaded face with the reference classroom group image """
    response = rekognition.compare_faces(
        SourceImage={'S3Object': {'Bucket': source_bucket, 'Name': source_key}},
        TargetImage={'S3Object': {'Bucket': target_bucket, 'Name': target_key}},
        SimilarityThreshold=80
    )
    return len(response['FaceMatches']) > 0


def check_name_in_text(bucket, image_key, student_name):
    """ Extracts text from an image and checks if student's name appears """
    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': image_key}}
    )

    extracted_text = " ".join([item["DetectedText"] for item in response["Blocks"] if item["BlockType"] == "LINE"])
    return student_name.lower() in extracted_text.lower()


def record_participation(name, email, meeting_date):
    """ Inserts a participation record into DynamoDB """
    table.put_item(
        Item={
            "name": name,
            "email": email,
            "meeting_date": meeting_date,
            "participation": True
        }
    )
