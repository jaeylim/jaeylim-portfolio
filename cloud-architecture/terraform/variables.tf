variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "project_name" {
  description = "Resource naming prefix"
  type        = string
  default     = "tf3tier"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.2.0.0/16"
}

variable "azs" {
  description = "Availability zones used (2 AZ)"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.0.0/24", "10.2.1.0/24"]
}

variable "app_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.2.0/24", "10.2.3.0/24"]
}

variable "db_subnet_cidrs" {
  type    = list(string)
  default = ["10.2.6.0/24", "10.2.7.0/24"]
}

variable "ec2_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "db_username" {
  type    = string
  default = "appadmin"
}

variable "db_password" {
  description = "DB master password (do not commit real values; pass via -var or TF_VAR_db_password)"
  type        = string
  sensitive   = true
}

variable "key_pair_name" {
  description = "Existing EC2 key pair name for SSH access"
  type        = string
  default     = null
}
