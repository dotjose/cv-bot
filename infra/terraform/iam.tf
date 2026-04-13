resource "aws_iam_role" "lambda" {
  name = "${local.name_prefix}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_memory_s3" {
  statement {
    sid    = "ChatMemoryS3"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.memory.arn,
      "${aws_s3_bucket.memory.arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_memory_s3" {
  name   = "${local.name_prefix}-lambda-memory-s3"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_memory_s3.json
}
